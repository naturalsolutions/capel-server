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

from dbcredentials import dbcredentials as dba


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{dba}localhost/portcros'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWTSECRET'] = b'abcdef'
app.config['AUTH_TYPE'] = 'Bearer'
app.config['REFRESH_TK_TTL'] = datetime.timedelta(seconds=30)
# app.config['ACCESS_TK_TTL'] = datetime.timedelta(seconds=30)
app.config['MIN_PWD_LEN'] = 6
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

            if token is None or auth_type != app.config['AUTH_TYPE']:
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
        return make_response('Could not authenticate.', 401, {
            'WWW-Authenticate': f'{app.config["AUTH_TYPE"]} realm="CAPEL login required"'})  # noqa

    # User submitted a valid password
    if (user is None or
            not hmac.compare_digest(
                user.password, request.json['password'])):
        return jsonify(error='Wrong credentials.'), 404

    utc_now = datetime.datetime.utcnow()
    token = jwt.encode({
        'id': user.id,
        'exp': utc_now + app.config['REFRESH_TK_TTL']},
        app.config['JWTSECRET'], algorithm='HS256')

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
        user = request.get_json()
    else:
        user = reqUser

    try:
        if (reqUser is None and
            (user.get('password') in (None, '') or
             len(user['password']) < app.config['MIN_PWD_LEN'] or
             user.get('email') in (None, '') or not re.match(
                app.config['VALID_EMAIL_REGEX'], user['email'], re.I))):
            return jsonify(error='Empty or malformed required field.'), 400

        valid_boats = None
        boats = user.get('boats', None)
        if (boats is not None):
            for boat in boats:
                if (boat is None or boat.get('name') in (None, '') or
                        boat.get('immatriculation') in (None, '')):
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
        # FIXME: #lowerprio, https://www.pivotaltracker.com/story/show/156689324/comments/188344433  # noqa
        etype, value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(etype, value)))
        return jsonify(str(e.orig)), 400

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
