#!/usr/bin/python3
import datetime
import re
from functools import wraps
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
import jwt
import hmac

from dbcredentials import dbcredentials as dba


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{dba}localhost/portcros'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWTSECRET'] = b'abcdef'
app.config['AUTH_TYPE'] = 'Bearer'
app.config['REFRESH_TK_TTL'] = datetime.timedelta(seconds=30)
app.config['ACCESS_TK_TTL'] = datetime.timedelta(seconds=30)
app.config['MIN_PWD_LEN'] = 6
app.config['VALID_EMAIL_REGEX'] = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

    def toJSON(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email
        }


def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        auth_type, token = request.headers.get('Authorization').split(' ', 1)

        if auth_type != app.config['AUTH_TYPE'] or token is None:
            return jsonify('', 401)

        try:
            payload = jwt.decode(
                request.json['payload'],
                key=app.config['JWTSECRET'], algorithm='HS256')
        except jwt.ExpiredSignatureError:
            return jsonify(reason='Token expired'), 401
        except jwt.InvalidTokenError:
            return jsonify(reason='Invalid token.'), 401

        user = User.query.filter_by(id=payload['id']).first()

        if user is None:
            return jsonify(reason='Unknown user'), 401

        return f(*args, user)
    return decorated_function


def authenticateOrNot(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if token is None:
            return f(*args, None)

        token = token.split(' ', 1)

        if not request.json['payload']:
            return jsonify(reason='No data.'), 400

        try:
            payload = jwt.decode(
                request.json['payload'],
                key=app.config['JWTSECRET'], algorithm='HS256')
        except jwt.ExpiredSignatureError:
            return jsonify(reason='Token Expired.'), 401
        except jwt.InvalidTokenError:
            return jsonify(reason='Invalid token.'), 401

        user = User.query.filter_by(id=payload['id']).first()

        if user is None:
            return jsonify(''), 403

        return f(*args, user)
    return decorated_function


@app.route("/")
def hello():
    return 'hello portcros-server !'


@app.route('/api/users/login', methods=['POST'])
def login():

    # Required fields
    if (len(request.json['password']) == 0 or len(request.json['email']) == 0):
        return jsonify(), 400

    # User exists and submitted a valid password
    try:
        user = User.query.filter(
            or_(
                User.username == request.json['email'],
                # User.username == request.json['username'],
                # User.email == request.json['username'],
                User.email == request.json['email']
            )
        ).first()
    except Exception as e:
        return jsonify(str(e.args)), 404
        # return jsonify(reason='Unregistered user.'), 404

    print('User:', f'{user.username}:{user.password}')

    if (user is None or
            not hmac.compare_digest(
                user.password, request.json['password'])):
        return jsonify(reason='Wrong credentials.'), 404

    user.username = user.email  # !!!
    payload = user.toJSON()

    utc_now = datetime.datetime.utcnow()
    token = jwt.encode({
        'id': user.id,
        'exp': utc_now + app.config['REFRESH_TK_TTL']},
        app.config['JWTSECRET'], algorithm='HS256')

    return jsonify(token=token.decode('utf-8'), payload=payload)


@app.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)


@app.route('/api/users', methods=['POST'])
@authenticateOrNot
def postUsers(reqUser):
    # Signup
    user = request.get_json()
    print('user post:', user)
    if (len(user['password']) < app.config['MIN_PWD_LEN'] or
            len(user['email']) == 0 or not re.match(
                app.config['VALID_EMAIL_REGEX'], user['email'], re.IGNORECASE)):  # noqa
        return jsonify(reason='Empty or malformed required field.'), 400

    user = User(**user)
    if not user.username:
        user.username = user.email
    user.password = make_digest(user.password)
    # TODO: user.created = datetime.datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        return jsonify(str(e.orig)), 400  # FIXME: #lowerprio, see https://www.pivotaltracker.com/story/show/156689324/comments/188344433  # noqa

    return jsonify(user=user.toJSON())


@app.route('/api/users', methods=['GET'])
@authenticate
def getUsers(reqUser):
    users = User.query.all()
    results = []
    for user in users:
        results.append(user.toJSON())

    return jsonify(results)


def make_digest(msg):
    return hmac.new(
        app.config['JWTSECRET'],
        msg=msg.encode(),
        digestmod='sha256').hexdigest()
