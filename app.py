#!/usr/bin/python3

import os
from flask import Flask, jsonify
from flask_cors import CORS


VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
WELCOME_EMAIL_SUBJECT = 'Bienvenue sur CAPEL'
WELCOME_EMAIL_TEMPLATE = 'assets/welcome_email_template.html'
REMINDER_EMAIL_SUBJECT = 'Valider votre compte'
REMINDER_EMAIL_TEMPLATE = WELCOME_EMAIL_TEMPLATE

app = Flask(__name__)
CORS(app)

app.config.from_object('conf')
if os.environ.get('CAPEL_CONF', None):
    app.config.from_envvar('CAPEL_CONF')
from model import (db, migrate, TypeDive)  # noqa
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


@app.route('/api/devies/typedives')
def getTypeDives():
    typeDives = TypeDive.query.all()
    typeDivesJsn = []
    for typeDive in typeDives:
        typeDivesJsn.append(typeDive.toJSON())
    return jsonify(typeDivesJsn)
