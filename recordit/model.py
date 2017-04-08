import math

from datetime import datetime, timedelta
from sqlalchemy import Column, DateTime, String, Integer, func, event
from sqlalchemy.ext.declarative import declarative_base
from eve_sqlalchemy.decorators import registerSchema
from celery.contrib.abortable import AbortableAsyncResult

from .worker import record


_Base = declarative_base()


# columns required by eve
class Base(_Base):
    __abstract__ = True
    _id = Column(Integer, primary_key=True, autoincrement=True)
    _created = Column(DateTime, default=func.now())
    _updated = Column(DateTime, default=func.now(), onupdate=func.now())
    _etag = Column(String(40))


@registerSchema('recording')
class Recording(Base):
    __tablename__ = 'recording'
    # task id, used to query task status
    _task = Column(String(36))
    name = Column(String(40), nullable=False, unique=True)
    url = Column(String(400), nullable=False)
    # time to start recording at the first time, immediately if null
    start = Column(DateTime, default=func.now())
    # total seconds to record, infinite if null
    duration = Column(Integer)
    # interval seconds between start time of multiple recordings,
    # not to repeat if null
    interval = Column(Integer)

    @classmethod
    def from_dict(cls, obj: dict):
        ret = cls()
        for key, val in obj.items():
            try:
                setattr(ret, key, val)
            except:
                pass
        return ret

    def result(self):
        if self._task is not None:
            return AbortableAsyncResult(self._task)

    def next_start_time(self):
        '''
        find the least `start` that:
        1. now - start < self.duration
        2. start = self.start + k * self.interval (k is a non-negative integer)
        '''
        now = datetime.utcnow()

        # no repeat, so start_time is always this.start
        if self.interval is None:
            return self.start

        duration = self.duration or 0

        # now - start < self.duration
        k = math.ceil(
            ((now - self.start).total_seconds() - duration)
            / self.interval)
        # k is a non-negative
        k = max(k, 0)

        return self.start + k * timedelta(seconds=self.interval)


@event.listens_for(Recording, 'before_insert')
def add_task(mapper, connection, target):
    # There is a subtle race-condition
    if target.duration is None:
        start_time = target.start
    else:
        start_time = target.next_start_time()

    kwargs = {
        'web_video': target.url,
        'dump_file': f'{target.name}-{start_time}.mp4',
    }
    if target.duration is not None:
        kwargs['until'] = start_time + timedelta(seconds=target.duration)

    result = record.apply_async(kwargs=kwargs, eta=start_time)
    target._task = result.id
