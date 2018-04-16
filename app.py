#!/usr/bin/python3

import sys
import datetime
import re
from traceback import format_exception_only
from functools import wraps
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy  # , UUID
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
import jwt
import hmac
import json
# import uuid

try:
    from dbcredentials import dbcredentials as dba
except Exception:
    dba = None


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{dba}localhost/portcros'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWTSECRET'] = b'abcdef'
app.config['JWT_AUTH_TYPE'] = 'Bearer'
app.config['JWT_REFRESH_EXP'] = datetime.timedelta(seconds=30)
# app.config['JWT_ACCESS_EXP'] = datetime.timedelta(seconds=30)
app.config['VALID_PWD_MIN_LEN'] = 6
app.config['VALID_EMAIL_REGEX'] = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # uid = db.Column(UUID(as_uuid=True), primary_key=True,
    #                 default=lambda: uuid.uuid4().hex)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    boats = db.Column(db.String(255))

    def __repr__(self):
        return '<User %r>' % self.username

    def toJSON(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'boats': self.boats
        }


def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        try:
            auth_type, token = request.headers.get('Authorization').split(' ', 1)  # noqa

            if token is None or auth_type != app.config['JWT_AUTH_TYPE']:
                return jsonify(error='Invalid token.'), 401

            payload = jwt.decode(
                token, key=app.config['JWTSECRET'], algorithm='HS256')

            user = User.query.filter_by(id=payload['id']).first()
            if user is None:
                return jsonify(error='Could not authenticate.'), 401

        except Exception:
            return jsonify(error='Could not authenticate.'), 401

        return f(user, *args, **kwargs)
    return decorated_function


def authenticateOrNot(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        try:
            token = request.headers.get('Authorization')

            if token is None:
                return f(None, *args, **kwargs)

            token = token.split(' ', 1)

            payload = jwt.decode(
                token, key=app.config['JWTSECRET'], algorithm='HS256')

            user = User.query.filter_by(id=payload['id']).first()
            if user is None:
                return jsonify(error='Could not authenticate.'), 403

        except jwt.ExpiredSignatureError:
            return jsonify(error='Token Expired.'), 401
        except Exception:
            return jsonify(error='Could not authenticate.'), 401

        return f(user, *args, **kwargs)
    return decorated_function


@app.route("/")
def hello():
    return 'hello portcros-server !'


@app.route('/api/users/login', methods=['POST'])
def login():
    user = None

    try:
        if request.json is None:
            return jsonify(error='Invalid JSON.')
    except Flask.JSONBadRequest:
        return jsonify(error='Invalid JSON.')

    # Required fields
    if (request.json.get('password') in (None, '') or
            request.json.get('email') in (None, '')):
        return jsonify(), 400

    # User is already registered
    try:
        user = User.query.filter(User.email == request.json['email']).first()
    except Exception as e:
        return make_response(
            'Could not authenticate.', 401,
            {'WWW-Authenticate': f'{app.config["JWT_AUTH_TYPE"]}'
                                 ' realm="CAPEL login required"'})

    # User submitted a valid password
    if (user is None or
            not hmac.compare_digest(
                user.password, request.json['password'])):
        return jsonify(error='Wrong credentials.'), 404

    token = renew_refresh_token(user.id)
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
    if reqUser is None:
        try:
            user = request.get_json()
        except Flask.JSONBadRequest:
            return jsonify(error='Invalid JSON.')
    else:
        user = reqUser

    try:
        if (reqUser is None and not validate_user_create(user)):
            app.logger.debug(user)
            return jsonify(error='Empty or malformed required field.'), 400

        valid_boats = None
        boats = user.get('boats', None)
        if (boats is None or not isinstance(boats, list)
                or not validate_boats(boats)):
            app.logger.warn('User boats declaration error.')
            raise

        valid_boats = json.dumps(boats)
        user['boats'] = valid_boats

        user = User(**user)
        if not user.username:
            user.username = user.email
        user.password = make_digest(user.password)

    except Exception:
        return jsonify(error='Empty or malformed required field.'), 400

    try:
        if reqUser is None:
            db.session.add(user)
        else:
            db.session.merge(user)
        db.session.commit()
    except (IntegrityError, Exception) as e:
        db.session.rollback()
        # FIXME: #lowerprio, https://www.pivotaltracker.com/story/show/156689324/comments/188344433  # noqa
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))
        return jsonify(str(e.orig)), 400

    if reqUser:
        token = renew_refresh_token(user.id)
        return jsonify(token=token.decode('utf-8'), user=user.toJSON())
    else:
        return jsonify(user.toJSON())


@app.route('/api/users', methods=['GET'])
@authenticate
def getUsers(reqUser):
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


def make_digest(msg):
    return hmac.new(
        app.config['JWTSECRET'],
        msg=msg.encode(),
        digestmod='sha256').hexdigest()


def renew_refresh_token(key):
    utc_now = datetime.datetime.utcnow()
    return jwt.encode({
        'id': key,
        'exp': utc_now + app.config['JWT_REFRESH_EXP']},
        app.config['JWTSECRET'], algorithm='HS256')


def validate_user_create(user):
    return (user.get('password') not in (None, '') and
            len(user['password']) >= app.config['VALID_PWD_MIN_LEN'] and
            user.get('email') not in (None, '') and
            re.match(
                app.config['VALID_EMAIL_REGEX'], user['email'], re.I))


def validate_boats(boats):
    for boat in boats:
        if (boat in (None, '') or
            boat.get('name') in (None, '') or
                boat.get('immatriculation') in (None, '')):
            return False
    return True
