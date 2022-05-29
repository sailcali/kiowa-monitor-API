#!/var/www/kiowa-monitor-API/venv/bin/python3

import gzip
from sh import pg_dump
with gzip.open('backup.gz', 'wb') as f:
    pg_dump('-U', 'postgres', 'kiowa_monitor', _out=f)
