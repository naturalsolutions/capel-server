# capel-server

## Setup

### Install database and packages dependancies

#### Linux
```sh
sudo apt install postgresql postgresql-contrib libpq-dev postgresql-9.6-postgis-scripts git-all
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```
```sql
sudo -u postgres psql postgres
CREATE DATABASE capel;
\c capel
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
\q
```
```sh
mkdir capel-venv
cd capel-venv
sudo /usr/bin/pip3 install virtualenv  # contemporary version:
virtualenv -p python3 .                # python3 -m venv capel-venv
source ./capel-venv/bin/activate
pip install psycopg2-binary geoalchemy2 Flask flask_sqlalchemy flask_cors pyjwt Flask-Migrate sendgrid reportlab PyPDF2 certifi
# IOS: Applications/Python\ 3.6/Install\ Certificates.command
```

### Clone repository
```sh
git clone https://github.com/NaturalSolutions/capel-server.git
```


## Configure
Create/edit app.conf
```sh
cd capel-server
```

```py
# sample conf
from datetime import timedelta
try:
  from credentials import dbcredentials as dba
except Exception:
  dba = 'postgres@'

SQLALCHEMY_DATABASE_URI = f'postgresql://{dba}localhost/capel'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWTSECRET = b'SECRET_ENCRYPTION_KEY'
JWT_AUTH_TYPE = 'Bearer'
JWT_ID_TK_EXP = timedelta(seconds=30)
VALID_PWD_MIN_LEN = 6
SENDGRID_API_KEY = 'SENDGRID_API_KEY'
WEBAPP_URL = 'WEBAPP_URL'
SERVER_URL = 'SERVER_URL'
PERMITS_DIR = 'permits'

```

## Run

```sh
cd capel-server
source ../capel-venv/bin/activate
export FLASK_APP=app.py
# export APP_DEBUG=true
# export CAPEL=/path/to/special_capel_conf.py
flask db init     # on first run
flask db migrate  # on subsequent runs with an updated db schema
flask db upgrade
flask run
```

## Annex: Heroku deployment
### Linux
```sh
curl https://cli-assets.heroku.com/install-standalone.sh | sh
heroku login
pip install gunicorn
echo 'web: gunicorn app:app' > Procfile
echo 'release: FLASK_APP=app.py flask db upgrade' >> Procfile
pip freeze > requirements.txt
# commit changes
```

### MO
```sh
# run app locally, interrupt with CTRL-C
heroku local   
# create "heroku" git remote
heroku create  
echo 'python-3.6.4' > runtime.txt
# install Heroku postgres free plan
heroku addons:create heroku-postgresql:hobby-dev
# Enable postgis extensions !
# Copy/paste DATABASE_URL value to app_conf.py SQLALCHEMY_DATABASE_URI
heroku config  
git commit -am 'Update SQLALCHEMY_DATABASE_URI from "heroku config".'
git push heroku <branchname>:master
# Ensure that at least one instance of the app is running
heroku ps:scale web=1  
heroku open
heroku logs
heroku apps:rename capel-beta
```
