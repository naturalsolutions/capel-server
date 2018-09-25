# capel-server

## Setup

### Install database and packages dependencies

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
heroku create capel-beta
echo 'python-3.6.4' > runtime.txt
# install Heroku postgres free plan
heroku addons:create heroku-postgresql:hobby-dev
```

#### Enable postgis extensions
```sh
heroku pg:psql --app capel-beta
```
```sql
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
\q
```
```sh
# Copy/paste DATABASE_URL value to app_conf.py SQLALCHEMY_DATABASE_URI
heroku config  
git commit -am 'Update SQLALCHEMY_DATABASE_URI from "heroku config".'
FLASK_APP=app.py flask db init
```
Patch migrations/env.py to ignore 'spatial_ref_sys' table.
```diff
--- a/migrations/env.py
+++ b/migrations/env.py
@@ -26,6 +26,11 @@ target_metadata = current_app.extensions['migrate'].db.metadata
 # can be acquired:
 # my_important_option = config.get_main_option("my_important_option")
 # ... etc.
+def include_object(object, name, type_, reflected, compare_to):
+    if (name == 'spatial_ref_sys'):
+        return False
+    else:
+        return True


 def run_migrations_offline():
@@ -41,7 +46,10 @@ def run_migrations_offline():

     """
     url = config.get_main_option("sqlalchemy.url")
-    context.configure(url=url)
+    context.configure(
+        url=url,
+        include_object=include_object
+    )

     with context.begin_transaction():
         context.run_migrations()
@@ -73,6 +81,7 @@ def run_migrations_online():
     context.configure(connection=connection,
                       target_metadata=target_metadata,
                       process_revision_directives=process_revision_directives,
+                      include_object=include_object,
                       **current_app.extensions['migrate'].configure_args)

     try:
```
Update lastest migrations/versions/<migration_id>.py with`import geoalchemy2`

```sh
FLASK_APP=app.py flask db migrate
git push heroku <branchname>:master
heroku run upgrade
# Ensure that at least one instance of the app is running
heroku ps:scale web=1  
heroku config:set WEB_CONCURRENCY=3
heroku open
heroku logs -t
```
#### To script
```sh
heroku run python -app <app name>
import os
db = os.environ.get('DATABASE_URL')

export DATABASE_URL = db
export FLASK_APP=app.py
flask db migrate
git push heroku master

PS: import geoalchemy2 in last migrate version
 ```
#### Add heart to divesite
```sh
 update divesites d1
set heart_id = d2.id
from divesites d2
where
st_contains(d2.geom_poly,  ST_GeomFromText('POINT(' || d1.longitude || ' ' ||d1.latitude || ')',4326))
	  and d1.category='site'
	  and d2.category='coeur'
	  and d2.status='enabled';
 ```    
 #### Trigger add heart to divesite when added
 ```sh
 CREATE OR REPLACE FUNCTION add_heart_to_site_function()
 RETURNS trigger AS
$$
BEGIN
update divesites d1
set heart_id = d2.id
from divesites d2
where
st_contains(d2.geom_poly,  ST_GeomFromText('POINT(' || d1.longitude || ' ' ||d1.latitude || ')',4326))
   and d1.category='site'
   and d2.category='coeur'
   and d2.status='enabled'
   and d1.id = NEW.id;

   RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

CREATE TRIGGER add_heart_to_site
 AFTER INSERT
 ON divesites
 FOR EACH ROW
 EXECUTE PROCEDURE add_heart_to_site_function();
  ```   
