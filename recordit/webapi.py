import os

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from celery.contrib.abortable import AbortableAsyncResult

from .model import Base, Recording


def query_task_status(response):
    response['state'] = AbortableAsyncResult(response['_task']).state


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

    app = Eve(settings=eve_settings, data=SQL, validator=ValidatorSQL)

    # bind SQLAlchemy
    db = app.data.driver
    db.Model = Base

    # try to create all tables
    db.create_all()

    app.on_fetched_item_recording = query_task_status

    return app


app = create_app()

if __name__ == '__main__':
    app.run()
