import os

from cerberus import Validator


class Config:
    def __init__(self):
        schema = {
            'DB': {
                'type': 'string',
                'default': f'sqlite:///{os.getcwd()}/recordit.db',
            },
        }
        v = Validator(schema, purge_unknown=True)

        self._cfg = v.normalized(os.environ)

    def __getitem__(self, x):
        return self._cfg[x]
