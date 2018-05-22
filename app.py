#!/usr/bin/python3

import os
from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config.from_object('conf')
if os.environ.get('CAPEL_CONF', None):
    app.config.from_envvar('CAPEL_CONF')

from model import (db, migrate)  # noqa
db.init_app(app)
migrate.init_app(app, db)

from assets import assets  # noqa
app.register_blueprint(assets)

from mail import mail  # noqa
app.register_blueprint(mail)

import api  # noqa
app.register_blueprint(api.api)
api.init_app(app)


@app.route("/")
def hello():
    return 'hello capel-server !'
