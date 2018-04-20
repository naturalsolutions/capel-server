#!/usr/bin/python3

import os
import sys
import datetime
import re
from traceback import format_exception_only
from functools import wraps
from flask import (Flask, jsonify, request, make_response, Response)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
import jwt
import hmac
import json


app = Flask(__name__)
CORS(app)
app.config.from_object('app_conf')
if os.environ.get('CAPEL_CONF', None):
    app.config.from_envvar('CAPEL_CONF')
db = SQLAlchemy(app)

VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
DUPLICATE_KEY_ERROR_REGEX = r'duplicate key value violates unique constraint \"[a-z_]+_key\"\nDETAIL:\s+Key \((?P<duplicate_key>.*)\)=\(.*\) already exists.'  # noqa


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    boats = db.Column(db.String(255))
    category = db.Column(db.String(64), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255))
    createdAt = db.Column(db.DateTime)

    def __repr__(self):
        return '<User %r>' % self.username

    def toJSON(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'boats': json.loads(self.boats)
        }


@app.before_first_request
def init_db():
    # Initialize database schema
    db.create_all()


def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header not in (None, ''):
            try:
                auth_type, token = auth_header.split(' ', 1)

                if token is None or auth_type != app.config['JWT_AUTH_TYPE']:
                    return jsonify(error='Invalid token.'), 401

                payload = jwt.decode(
                    token, key=app.config['JWTSECRET'], algorithm='HS256')
            except jwt.ExpiredSignatureError:
                return jsonify(error='Token Expired.'), 401
            except Exception:
                return jsonify(error='Could not authenticate.'), 401

            user = User.query.filter_by(id=payload['id']).first()

        if user is None:
            return jsonify(error='Could not authenticate.'), 401

        return f(user, *args, **kwargs)
    return decorated_function


def authenticateOrNot(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header not in (None, ''):
            try:
                auth_type, token = auth_header.split(' ', 1)
                if token is None or auth_type != app.config['JWT_AUTH_TYPE']:
                    return jsonify(error='Invalid token.'), 401
                app.logger.debug(token)
                token = token.split(' ', 1)

                payload = jwt.decode(
                    token, key=app.config['JWTSECRET'], algorithm='HS256')
            except jwt.ExpiredSignatureError:
                return jsonify(error='Token Expired.'), 401
            except Exception:
                return jsonify(error='Could not authenticate.'), 401

            user = User.query.filter_by(id=payload['id']).first()
            if user is None:
                return jsonify(error='Could not authenticate.'), 403

        return f(user, *args, **kwargs)
    return decorated_function


@app.route("/")
def hello():
    return 'hello portcros-server !'


@app.route('/api/users/login', methods=['POST'])
def login():
    user = None

    # Required fields
    if (request.json is None or
        request.json.get('password') in (None, '') or
            request.json.get('username') in (None, '')):
        return make_response(
            'Could not authenticate.', 401,
            {'WWW-Authenticate': f'{app.config["JWT_AUTH_TYPE"]}'
                                 ' realm="CAPEL login required"'})

    # Registered user
    try:
        user = User.query.filter_by(username=request.json['username']).first()
    except Exception as e:
        return make_response(
            'Could not authenticate bla.', 401,
            {'WWW-Authenticate': f'{app.config["JWT_AUTH_TYPE"]}'
                                 ' realm="CAPEL login required"'})
    if user is None:
        return jsonify(error='Wrong credentials.'), 401
    # Valid password
    if (user and not hmac.compare_digest(
            user.password, make_digest(request.json['password']))):
        return jsonify(error='Wrong credentials.'), 401

    token = generate_id_token(user.id)
    return jsonify(token=token.decode('utf-8'), profile=user.toJSON())


@app.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)


@app.route('/api/users', methods=['POST'])
@authenticateOrNot
def postUsers(reqUser):
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
        if (boats and
                (not isinstance(boats, list) or not validate_boats(boats))):
            return jsonify(
                error={'name': 'invalid_model',
                       'errors': [{'name': 'invalid_format', 'key': 'boats'}]}
            ), 400

        try:
            user['boats'] = json.dumps(boats)
        except TypeError:
            return jsonify(error='Invalid JSON.')

        user['password'] = make_digest(user['password'])
        user['status'] = 'draft'
        user['createdAt'] = datetime.datetime.utcnow()
        user = User(**user)

    except Exception as e:
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))
        return jsonify(error='Empty or malformed required field.'), 400

    try:
        db.session.add(user)
        db.session.commit()
    except (IntegrityError, Exception) as e:
        db.session.rollback()
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))
        err_orig = str(e.orig)
        error = err_orig

        if err_orig.find('violates unique constraint') > -1:
            error = {'name': 'value_exists',
                     'key': unique_constraint_key(err_orig)}

        elif err_orig.find('violates not-null constraint') > -1:
            error = {'name': 'missing_attribute',
                     'key': not_null_constraint_key(err_orig)}

        return jsonify(error={'name': 'invalid_model', 'errors': [error]}), 400

    return jsonify(user.toJSON())


@app.route('/api/users', methods=['GET'])
@authenticateOrNot
def getUsers(reqUser):
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


@app.route('/api/users/<username>/permit.pdf', methods=['GET'])
@authenticate
def getPermit(reqUser, username=None):
    from pdfgen import DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)
    response = None
    user = User.query.filter_by(username=username).first_or_404()
    name = '_'.join([user.firstname, user.lastname])
    if user is not None:
        f = f'{DATA_DIR}/permit_{name}.pdf'
        # app.logger.debug('pdf_file', f)
        if not os.path.isfile(f):
            from pdfgen import Diver, Permit
            diver = Diver(
                user.lastname,
                user.firstname,
                user.email,
                user.phone)
            boat = None
            permit = Permit(diver, boat)
            permit.save()

        try:
            with open(f, 'rb') as pdf:  # noqa
                response = Response(pdf.read())
                response.mimetype = 'application/pdf'
                response.headers['Content-Disposition'] = (
                    'attachment; filename={}'.format(os.path.basename(f)))
                return response
        except Exception as e:
            err_type, err_value, tb = sys.exc_info()
            app.logger.warn(''.join(format_exception_only(err_type, err_value)))  # noqa
            return '500 error', 500


def make_digest(msg):
    return hmac.new(
        app.config['JWTSECRET'],
        msg=msg.encode(),
        digestmod='sha256').hexdigest()


def generate_id_token(key):
    utc_now = datetime.datetime.utcnow()
    return jwt.encode({
        'id': key,
        'exp': utc_now + app.config['JWT_ID_TK_EXP']},
        app.config['JWTSECRET'], algorithm='HS256')


def users_validate_required(user):
    errors = []

    if (not user.get('category', None) or
            user.get('category', None) not in ('particulier', 'structure')):
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

    boat_validation = validate_boats(user.get('boats', []))
    if boat_validation['errors']:
        errors.extend(boat_validation['errors'])

    if len(errors) >= 0:
        return {'errors': errors}

    return True


def validate_boats(boats):
    errors = []

    for i, boat in enumerate(boats):
        if boat in (None, ''):
            errors.append({'name': 'invalid_format', 'key': f'boat[{i}]'})
            continue

        if boat.get('name') in (None, ''):
            errors.append({'name': 'invalid_format', 'key': f'boat[{i}].name'})

        if boat.get('matriculation') in (None, ''):
            errors.append({'name': 'invalid_format',
                           'key': f'boat[{i}].matriculation'})

    if len(errors) >= 0:
        return {'errors': errors}
    return True


def not_null_constraint_key(error):
    return error.split('violates not-null constraint')[0] \
                .split('column')[1].strip().replace('"', '')


def unique_constraint_key(error):
    m = re.search(DUPLICATE_KEY_ERROR_REGEX, error)
    return m.group('duplicate_key')
