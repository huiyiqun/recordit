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
    name = Column(String(40), nullable=False, unique=True)
    url = Column(String(400), nullable=False)
    _task = Column(String(36))
