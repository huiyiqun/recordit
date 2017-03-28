import os

from os import path
from flask import current_app
from eve import Eve
from eve_sqlalchemy import SQL
from sqlalchemy import Column, DateTime, String, Integer, func
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
def start_to_record(recordings):
    for r in recordings:
        current_app.logger.debug(r['url'])
        # TODO: check name
        result = record.delay(r['url'], path.join('.', r['name']+'.mp4'))
        # XXX: maybe we should be decoupled with eve_sqlalchemy
        current_app.data.update('recording', r['_id'], {'_task': str(result)}, None)

def stop_recording(recording):
    current_app.logger.debug(recording)
    task_id = recording['_task']
    if task_id is not None:
        result = AbortableAsyncResult(recording['_task'])
        result.abort()


def create_app():
    eve_settings = {
        'DEBUG': True,

        'DOMAIN': {
            'recording': {
                **Recording._eve_schema['recording'],
                'resource_methods': ['GET', 'POST'],
                'item_methods': ['GET', 'DELETE'],
            },
        },

        # database
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{os.getcwd()}/recordit.db',
        # suggested by flask_sqlalchemy
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,

        # cors
        'X_DOMAINS': '*',
        'X_HEADERS': ['Content-Type'],

        # ISO 8601
        'DATE_FORMAT': "%Y-%m-%dT%H:%M:%S.%fZ",

        # disable concurrency control
        'IF_MATCH': False,
    }

    app = Eve(settings=eve_settings, data=SQL)

    # bind SQLAlchemy
    db = app.data.driver
    db.Model = Base

    # try to create all tables
    db.create_all()

    # bind hooks
    app.on_inserted_recording = start_to_record
    app.on_deleted_item_recording = stop_recording

    return app


app = create_app()

if __name__ == '__main__':
    app.run()
