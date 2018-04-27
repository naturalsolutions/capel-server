# capel-server

## Setup

### Install database and packages depencies

#### Linux
```sh
sudo apt install postgresql postgresql-contrib libpq-dev postgresql-9.6-postgis-scripts
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
pip install psycopg2-binary geoalchemy2 Flask flask_sqlalchemy flask_cors pyjwt Flask-Migrate sendgrid reportlab PyPDF2
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

# to resolve sendgrid problem: SSL: CERTIFICATE_VERIFY_FAILED” Error

```sh
pip install certifi
/Applications/Python\ 3.6/Install\ Certificates.command
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
# Enable postgis extension

-- Enable PostGIS (includes raster)
CREATE EXTENSION postgis;
-- Enable Topology
CREATE EXTENSION postgis_topology;
-- Enable PostGIS Advanced 3D
-- and other geoprocessing algorithms
-- sfcgal not available with all distributions
CREATE EXTENSION postgis_sfcgal;
-- fuzzy matching needed for Tiger
CREATE EXTENSION fuzzystrmatch;
-- rule based standardizer
CREATE EXTENSION address_standardizer;
-- example rule data set
CREATE EXTENSION address_standardizer_data_us;
-- Enable US Tiger Geocoder
CREATE EXTENSION postgis_tiger_geocoder;
