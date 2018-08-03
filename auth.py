#!/usr/bin/python3
import datetime
from functools import wraps
import hmac
import jwt
from flask import (request, jsonify, current_app)

from model import User

__all__ = [
    'generate_id_token',
    'generate_token',
    'authenticate',
    'authenticateOrNot']


def generate_id_token(id):
    return generate_token(
        id,
        current_app.config['JWT_ID_TK_EXP'],
        current_app.config['JWTSECRET'])


def generate_token(id, duration, secret):
    utc_now = datetime.datetime.utcnow()
    return jwt.encode(
        {'id': id, 'exp': utc_now + duration}, secret, algorithm='HS256')


def make_digest(msg):
    return hmac.new(
        current_app.config['JWTSECRET'],
        msg=msg.encode(),
        digestmod='sha256').hexdigest()


def compare_digest(a, b):
    return hmac.compare_digest(a, b)


def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header not in (None, ''):
            try:
                auth_type, token = auth_header.split(' ', 1)

                if (token is None or
                        auth_type != current_app.config['JWT_AUTH_TYPE']):
                    return jsonify(error='Invalid token.'), 401

                payload = jwt.decode(
                    token,
                    key=current_app.config['JWTSECRET'],
                    algorithm='HS256')
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
        if request.headers.get('Authorization') is None:
            return f(None, *args, **kwargs)
        user = None
        try:
            auth_type, token = request.headers.get('Authorization')\
                                              .split(' ', 1)

            if (token is None or
                    auth_type != current_app.config['JWT_AUTH_TYPE']):
                return jsonify(error='Invalid token.'), 401

            payload = jwt.decode(
                token, key=current_app.config['JWTSECRET'], algorithm='HS256')

            user = User.query.filter_by(id=payload['id']).first()
            if user is None:
                return jsonify(error='Could not authenticate.'), 401

        except Exception:
            return jsonify(error='Could not authenticate.'), 401

        return f(user, *args, **kwargs)
    return decorated_function

def authenticateAdmin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Authorization') is None:
            return f(None, *args, **kwargs)
        user = None
        try:
            auth_type, token = request.headers.get('Authorization')\
                                              .split(' ', 1)

            if (token is None or
                    auth_type != current_app.config['JWT_AUTH_TYPE']):
                return jsonify(error='Invalid token.'), 401

            payload = jwt.decode(
                token, key=current_app.config['JWTSECRET'], algorithm='HS256')

            user = User.query.filter_by(id=payload['id']).first()
            if user.role != 'admin':
                return jsonify(error='Could not authenticate.'), 401

        except Exception:
            return jsonify(error='Could not authenticate.'), 401

        return f(user, *args, **kwargs)
    return decorated_function
