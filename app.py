#!/usr/bin/python3

import os
import sys
import datetime
import re
from traceback import format_exception_only
from flask import (Flask, make_response, jsonify, request)
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from datetime import timedelta


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

from model import (
    db, migrate, User, Boat, TypeDive,
    unique_constraint_key, not_null_constraint_key)  # noqa
db.init_app(app)
migrate.init_app(app, db)

from auth import (
    authenticate, authenticateOrNot,
    generate_token, generate_id_token, make_digest, compare_digest)  # noqa

from asset import assets  # noqa
app.register_blueprint(assets)


import permit  # noqa
app.register_blueprint(permit.permit)
permit.init_app(app)

from mail import EmailTemplate, sendmail, mail  # noqa
app.register_blueprint(mail)

from dive import dives  # noqa
app.register_blueprint(dives)


@app.route("/")
def hello():
    return 'hello capel-server !'


@app.route('/api/users/login', methods=['POST'])
def login():
    user = None

    # Required fields
    if (request.json is None or
        request.json.get('password') in (None, '') or
            request.json.get('username') in (None, '')):
        return make_response('Could not authenticate.', 401)

    # Registered user
    try:
        user = User.query.filter_by(username=request.json['username']).first()
    except Exception as e:
        return make_response(
            'Could not authenticate bla.', 401)
    if user is None:
        return jsonify(error='Not registered.'), 401

    # Valid password
    if (user and not compare_digest(
            user.password, make_digest(request.json['password']))):
        return jsonify(error='Wrong credentials.'), 401

    if user and user.status == 'draft':

        emailToken = generate_token(
            user.id, timedelta(seconds=60 * 60 * 24),
            app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

        emailBody = EmailTemplate(
            template=REMINDER_EMAIL_TEMPLATE,
            values={
                'title': REMINDER_EMAIL_SUBJECT,
                'firstname': user.firstname,
                'serverUrl': app.config['SERVER_URL'],
                'token': emailToken
            }).render()

        sendmail(
            'no-reply@natural-solutions.eu', user.email,
            REMINDER_EMAIL_SUBJECT, emailBody)

        return jsonify(error='user_draft'), 403

    token = generate_id_token(user.id)
    return jsonify(token=token.decode('utf-8'), profile=user.toJSON())


@app.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)


@app.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    userPatch = request.get_json()
    User.query.filter_by(id=reqUser.id).update(userPatch)
    db.session.commit()
    user = User.query.filter_by(id=reqUser.id).first()
    return jsonify(user.toJSON())


@app.route('/api/users', methods=['POST'])
def postUsers():
    # Signup/Register
    try:
        user = request.get_json()
    except Exception:
        return jsonify(error='Invalid JSON.')

    try:
        if not user.get('username', None):
            user['username'] = user.get('email')
        validation = users_validate_required(user)
        if validation['errors']:
            return jsonify(error={'name': 'invalid_model',
                                  'errors': validation['errors']}), 400

        boats = user.get('boats', None)
        validation = validate_boats(boats)
        if boats:
            if (validation and validation['errors']):
                return jsonify(
                    error={'name': 'invalid_model',
                           'errors': validation['errors']}), 400

            user['boats'] = [Boat(**boat) for boat in boats]

        user['status'] = 'draft'
        user['createdAt'] = datetime.datetime.utcnow()
        user['password'] = make_digest(user['password'])
        user = User(**user)

    except Exception as e:
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))

        if err_type == 'TypeError':
            return jsonify(error='Invalid JSON.'), 400

        return jsonify(error='Empty or malformed required filed user.'), 400

    try:
        db.session.add(user)
        db.session.commit()
    except (IntegrityError, Exception) as e:
        db.session.rollback()
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))
        err_orig = str(getattr(e, 'orig', 'register error'))
        errors = []

        if err_orig.find('violates unique constraint') > -1:
            errors.append({'name': 'value_exists',
                          'key': unique_constraint_key(err_orig)})

        elif err_orig.find('violates not-null constraint') > -1:
            errors.append({'name': 'missing_attribute',
                           'key': not_null_constraint_key(err_orig)})

        return jsonify(error={'name': 'invalid_model', 'errors': errors}), 400

    emailToken = generate_token(
        user.id, timedelta(seconds=60 * 60 * 24),
        app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

    emailBody = EmailTemplate(
        template=WELCOME_EMAIL_TEMPLATE,
        values={
            'title': WELCOME_EMAIL_SUBJECT,
            'firstname': user.firstname,
            'serverUrl': app.config['SERVER_URL'],
            'token': emailToken
        }).render()

    sendmail(
        'no-reply@natural-solutions.eu', user.email,
        WELCOME_EMAIL_SUBJECT, emailBody)

    return jsonify(user.toJSON())


@app.route('/api/users', methods=['GET'])
@authenticateOrNot
def getUsers(reqUser):
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


@app.route('/api/users/boats')
@authenticate
def getBoats(reqUser):
    boats = reqUser.boats.all()
    boatJsn = []
    for boat in boats:
        boatJsn.append(boat.toJSON())
    return jsonify(boatJsn)


@app.route('/api/devies/typedives')
def getTypeDives():
    typeDives = TypeDive.query.all()
    typeDivesJsn = []
    for typeDive in typeDives:
        typeDivesJsn.append(typeDive.toJSON())
    return jsonify(typeDivesJsn)


def users_validate_required(user):
    errors = []

    if (not user.get('category', None) or
            user.get('category') not in ('particulier', 'structure')):
        errors.append({'name': 'invalid_format', 'key': 'category'})

    if len(user['password']) < app.config['VALID_PWD_MIN_LEN']:
        errors.append({'name': 'invalid_format', 'key': 'password',
                       'message': 'Password length must be >= ' +
                                  app.config['VALID_PWD_MIN_LEN']})

    if not re.match(VALID_EMAIL_REGEX, user['email'], re.I):
        errors.append({'name': 'invalid_format', 'key': 'email'})

    for attr in ('lastname', 'firstname', 'address', 'phone'):
        if not user.get(attr, None):
            errors.append({'name': 'invalid_format', 'key': attr})

    if len(errors) >= 0:
        return {'errors': errors}

    return True


def validate_boats(boats):
    errors = []

    for i, boat in enumerate(boats):
        if boat in (None, ''):
            errors.append(
                {'name': 'invalid_format', 'key': f'boat at index {i}'})
            continue

        elif boat.get('name') in (None, ''):
            errors.append({'name': 'invalid_format', 'key': boat[i].name})

        elif boat.get('matriculation') in (None, ''):
            errors.append(
                {'name': 'invalid_format', 'key': boat[i].matriculation})

    if len(errors) >= 0:
        return {'errors': errors}
    return True
