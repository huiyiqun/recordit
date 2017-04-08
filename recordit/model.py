from sqlalchemy import Column, DateTime, String, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from eve_sqlalchemy.decorators import registerSchema


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
    # interval seconds between start time of multiple recordings, not to repeat if null
    interval = Column(Integer)
