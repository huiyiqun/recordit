from os import path
from flask import current_app
from sqlalchemy import Column, DateTime, String, Integer, func, event
from sqlalchemy.ext.declarative import declarative_base
from eve_sqlalchemy.decorators import registerSchema
from celery.contrib.abortable import AbortableAsyncResult

from .record import record


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
    name = Column(String(40), nullable=False, unique=True)
    url = Column(String(400), nullable=False)
    _task = Column(String(36))


# hooks for db operations
@event.listens_for(Recording, 'before_insert', retval=True)
def start_to_record(mapper, connection, recording):
    current_app.logger.debug(recording)
    # TODO: check name
    result = record.delay(
        recording.url, path.join('.', recording.name+'.mp4'))
    # XXX: maybe we should be decoupled with eve_sqlalchemy
    recording._task = str(result)

    return recording


@event.listens_for(Recording, 'after_delete')
def stop_recording(mapper, connection, recording):
    current_app.logger.debug(recording)
    task_id = recording._task
    if task_id is not None:
        result = AbortableAsyncResult(recording._task)
        result.abort()
