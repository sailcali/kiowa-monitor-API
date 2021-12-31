import gzip
from sh import pg_dump
with gzip.open('backup.gz', 'wb') as f:
    pg_dump('-h', 'localhost', '-U', 'postgres', 'kiowa_monitor', _out=f)
