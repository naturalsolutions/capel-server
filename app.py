#!/usr/bin/python3
import datetime
from functools import wraps
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
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

        user = User.query.filter_by(username=payload['id']).first()

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
    if (len(request.json['password']) == 0 or
            len(request.json['username']) == 0):
        return jsonify(), 400

    # User exists and submitted a valid password
    try:
        user = User.query.filter_by(username=request.json['username']).first()
    except Exception as e:
        return jsonify(reason='User already registered.'), 404

    if (user is None or
            not hmac.compare_digest(
                user.password, make_digest(request.json['password']))):
        return jsonify(reason='Wrong credentials.'), 404

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
    print('reqUser', reqUser,
          'user', user,
          'r.json[]', request.json['username'])
    # if (len(user['password']) < app.config['MIN_PWD_LEN'] or
    #         len(user['username']) == 0 or len(user['email'] == 0 or
    #         not app.config['VALID_EMAIL_REGEX'].match(user['email']))):  # noqa
    #     return jsonify(reason='Required field empty.'), 400

    user = User(**user)
    user.password = make_digest(user.password)
    # user.created = datetime.datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        return jsonify(str(e.orig)), 400

    auth_token = jwt.encode({user.id: user.username}, app.config['JWTSECRET'], algorithm='HS256')  # noqa
    return jsonify(user=user.toJSON(), token=auth_token.decode('utf-8'))


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

