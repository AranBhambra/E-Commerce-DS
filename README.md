## Development

Replace the username and password with yours

### schema migration

```
mysql --user="root" --password="12345678" ears < schema.sql
```

### database seeding

```
mysql --user="root" --password="12345678" ears < seed.sql
```

### db reset

in case you want to clean up data for development

```
mysql --user="root" --password="12345678" ears < reset.sql
```


pip install requests

### find PID of port in use
lsof -i :8000
lsof -i :8001
lsof -i :8002

### kill port in use PID
kill -9 <PID>

### Start a server
python3 server.py --server A
python3 server.py --server B
python3 server.py --server C