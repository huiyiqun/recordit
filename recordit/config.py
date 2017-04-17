import os

from sqlalchemy import create_engine
from schema import Schema, Use, Optional


class Config:
    def __init__(self):
        schema = Schema({
            Optional(
                'DB',
                default=f'sqlite:///{os.getcwd()}/recordit.db'
            ): Use(create_engine)
        }, ignore_extra_keys=True)
        self._cfg = schema.validate(dict(os.environ))

    def __getitem__(self, x):
        return self._cfg[x]
