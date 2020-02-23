import os
import configparser
from urllib.parse import quote

# Initialise Config File
cfg = configparser.RawConfigParser()
cfg.read('.env')

# Get DB Configuration
DB_USER = cfg.get('database', 'DB_USER')
DB_PASS = cfg.get('database', 'DB_PASS')
DB_HOST = cfg.get('database', 'DB_HOST')
DB_NAME = cfg.get('database', 'DB_NAME')


def create_yoyo_config():
    cfg = configparser.RawConfigParser()

    cfg['DEFAULT'] = {
        'database': f'mysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}',
        'sources': f'{os.getcwd()}/migrations',
        'verbosity': 3,
        'batch_mode': 'on',
        'editor': '/usr/bin/vim -f {}',
        'post_create_command': 'git add {}',
        'prefix': 'ipdb_'
    }

    with open('yoyo.ini', 'w') as configfile:
        cfg.write(configfile)


if __name__ == '__main__':
    create_yoyo_config()
