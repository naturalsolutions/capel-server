# capel-server

## Setup

### Install database and packages depencies

#### Linux
```sh
sudo apt install postgresql postgresql-contrib libpq-dev git-all
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```
```sql
sudo -u postgres psql postgres
CREATE DATABASE capel;
\q
```
```sh
mkdir capel-venv
cd capel-venv
sudo /usr/bin/pip3 install virtualenv
virtualenv -p python3 .
. ./capel-venv/bin/activate
pip install psycopg2-binary Flask flask_sqlalchemy flask_cors pyjwt Flask-Migrate sendgrid reportlab PyPDF2
```

### Clone repository
```sh
git clone https://github.com/NaturalSolutions/capel-server.git
```


## Configure
Create and edit app.conf
```sh
cd capel-server
```

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

## Heroku deployment

### Linux
```sh
curl https://cli-assets.heroku.com/install-standalone.sh | sh
heroku login
pip install gunicorn
echo 'web: gunicorn app:app' > Procfile
heroku local   # run app locally, interrupt with CTRL-C
heroku create  # create "heroku" git remote
git push heroku <git branch name>
```
