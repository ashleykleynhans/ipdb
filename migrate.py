# This script is deprecated in favour of the yoyo CLI tool which displays output
# of what it is actually doing

#from yoyo import read_migrations
#from yoyo import get_backend
#from urllib.parse import urlsplit, quote
#import configparser

#cfg = configparser.RawConfigParser()
#cfg.read('.env')
#
#DB_USER = cfg.get('database', 'DB_USER')
#DB_PASS = cfg.get('database', 'DB_PASS')
#DB_HOST = cfg.get('database', 'DB_HOST')
#DB_NAME = cfg.get('database', 'DB_NAME')
#
#backend = get_backend('mysql://' + DB_USER + ':' + quote(DB_PASS) + '@' + DB_HOST + '/' + DB_NAME)
#migrations = read_migrations('migrations')
#
#if len(migrations) == 0:
#    print("No database migrations to run")
#else:
#    print("Applying database migrations")
#    with backend.lock():
#        backend.apply_migrations(backend.to_apply(migrations))
#    print("DB migrations completed")
