# capel-server

## Setup

### Install database

#### Linux
```sh
sudo apt install postgresql postgresql-contrib libpq-dev
```
```sql
sudo -u postgres psql postgres
CREATE DATABASE capel;
```
```sh
mkdir capel-venv
cd capel-venv
sudo /usr/bin/pip3 install virtualenv
virtualenv -p python3 .
. ./capel-venv/bin/activate
pip install psycopg2-binary Flask flask_sqlalchemy flask_cors pyjwt
```

### Clone repository
```sh
git clone https://github.com/NaturalSolutions/capel-server.git
```


## Configure
Create and edit app.conf
```py
# sample conf
from credentials import dbcredentials as dba
from datetime import timedelta

SQLALCHEMY_DATABASE_URI = f'postgresql://{dba}localhost/capel'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWTSECRET = b'SECRET_ENCRYPTION_KEY'
JWT_AUTH_TYPE = 'Bearer'
JWT_ID_TK_EXP = timedelta(seconds=30)
VALID_PWD_MIN_LEN = 6
SENDGRID_API_KEY = 'SENDGRID_API_KEY'
WEBAPP_URL = 'WEBAPP_URL'
SERVER_URL = 'SERVER_URL'

```

## Run

```sh
cd capel-server
source ../capel-venv/bin/activate
export FLASK_APP=app.py
# export APP_DEBUG=true
# export CAPEL=/path/to/special_capel_conf.py
flask run
```
