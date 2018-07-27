import sys
import datetime
from traceback import format_exception_only
import string
import random
import traceback
from flask import (Blueprint, jsonify, request, current_app)
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from mail import EmailTemplate, sendmail
from model import (db, User, Boat, unique_constraint_key, not_null_constraint_key, unique_constraint_error)
from auth import ( make_digest, generate_token, generate_id_token,authenticate, compare_digest)
from validators import(validate_boats, users_validate_required)

users = Blueprint('users', __name__)

@users.route('/api/users', methods=['GET'])
@authenticate
def getUsers(reqUser):
    users = User.query.filter( User.status != 'deleted' ).all()
    return jsonify([user.json() for user in users])

@users.route('/api/users/count', methods=['GET'])
@authenticate
def get_count_users(reqUser):
    data = db.session.query(func.count(User.id)).scalar()
    return  jsonify(data)

@users.route('/api/users/boats')
@authenticate
def getBoats(reqUser):
    boats = reqUser.boats.all()
    boatJsn = []
    for boat in boats:
        boatJsn.append(boat.json())
    return jsonify(boatJsn)



@users.route('/api/users', methods=['POST'])
def post_users():
    # Signup/Register
    try:
        payload = request.get_json()
        # current_app.logger.debug(payload)
    except Exception:
        return jsonify(error='Invalid JSON.')

    try:
        if not payload.get('username', None):
            payload['username'] = payload.get('email')

        validation = users_validate_required(payload)
        if validation['errors']:
            return jsonify(error={'name': 'invalid_model',
                                  'errors': validation['errors']}), 400

        boats = payload.get('boats', None)
        validation = validate_boats(boats)
        if boats:
            if (validation and validation['errors']):
                return jsonify(
                    error={'name': 'invalid_model',
                           'errors': validation['errors']}), 400

            payload['boats'] = [Boat(**boat) for boat in boats]

        payload['status'] = 'draft'
        payload['password'] = make_digest(payload['password'])
        user = User(**payload)

    except Exception as e:
        err_type, err_value, tb = sys.exc_info()
        current_app.logger.warn(
            ''.join(format_exception_only(err_type, err_value)))

        if err_type == 'TypeError':
            return jsonify(error='Invalid JSON.'), 400

        return jsonify(error='Empty or malformed required field.'), 400

    try:
        db.session.add(user)
        db.session.commit()
    except (IntegrityError, Exception) as e:
        db.session.rollback()
        err_type, err_value, tb = sys.exc_info()
        current_app.logger.warn(
            ''.join(format_exception_only(err_type, err_value)))
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
        user.id, datetime.timedelta(seconds=60 * 60 * 24),
        current_app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

    emailBody = EmailTemplate(
        template=current_app.config['WELCOME_EMAIL_TEMPLATE'],
        values={
            'title': current_app.config['WELCOME_EMAIL_SUBJECT'],
            'firstname': user.firstname,
            'serverUrl': current_app.config['SERVER_URL'],
            'token': emailToken
        }).render()

    sendmail('no-reply@natural-solutions.eu', user.email,
             current_app.config['WELCOME_EMAIL_SUBJECT'], emailBody)

    return jsonify(user.json())


@users.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.json()
    return jsonify(reqUser)

@users.route('/api/users', methods=['DELETE'])
@authenticate
def deleteUsers(reqUser):
    '''
    if(reqUser.role != 'admin'):
         return jsonify(error={
                'errors': 'Not Authorized'
            }), 401
    '''
    try:
        ids = request.args.getlist('id[]')
        for id in ids:
            print(id)
            db.session.query(User).filter(User.id == int(id)).update({'status':'deleted'})
            db.session.commit()
        return jsonify('success'), 200
    except Exception:
        traceback.print_exc()
        return jsonify(error='Invalid JSON.'), 400

@users.route('/api/users', methods=['PATCH'])
@authenticate
def patchUsers(reqUser):
    users = request.get_json()
    for user in users:
        userPatch = {}
        for key, value in user.items():
            if value != '':
                userPatch[key] = value
        patchUser(userPatch, reqUser)
    return jsonify('success'), 200



@users.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    # userPatch = {key: value for key, value in request.get_json().items() if value != ''}
    userPatch = {}
    for key, value in request.get_json().items():
        if value != '':
            userPatch[key] = value

    userPatch['id'] = reqUser.id
    patchUser(userPatch, reqUser)
    user = User.query.filter_by(id=reqUser.id).first()
    return jsonify(user.json())

def patchUser(userPatch, reqUser):
    boats = userPatch['boats']
    del userPatch['boats']
    validate_boats(boats)
    if boats:
        boatsValidation = validate_boats(boats)
        if (boatsValidation and boatsValidation['errors']):
            return jsonify(error={
                'name': 'invalid_model',
                'errors': boatsValidation['errors']
            }), 400
        for i, boat in enumerate(boats):
            try:
                if boat.get('id', None):
                    Boat.query.filter_by(id=boat.get('id')).update(boat)
                else:
                    boat['user_id'] = reqUser.id
                    boatModel = Boat(**boat)
                    db.session.add(boatModel)
            # TODO factorize
            except (IntegrityError, Exception) as e:
                catch(e)

    try:
        db.session.query(User).filter(User.id == int(userPatch['id'])).update(userPatch)
        db.session.commit()
    # TODO factorize
    except (IntegrityError, Exception) as e:
        catch(e)

def catch(e):
    db.session.rollback()
    err_type, err_value, tb = sys.exc_info()
    current_app.logger.warn(
        ''.join(format_exception_only(err_type, err_value)))
    err_orig = str(getattr(e, 'orig', 'register error'))
    errors = []
    if err_orig.find('violates unique constraint') > -1:
        errorValue = unique_constraint_error(err_orig)
        errors.append(errorValue)

    elif err_orig.find('violates not-null constraint') > -1:
        errorValue = not_null_constraint_error(str(e))
        errors.append(errorValue)

    return jsonify(error={'name': 'invalid_model', 'errors': errors}), 400

@users.route('/api/users/login', methods=['POST'])
def log_in():
    user = None

    # Required fields
    if (request.json.get('password') in (None, '') or
            request.json.get('username') in (None, '')):
        return jsonify(error='Could not authenticate.'), 401

    # Registered user
    try:
        user = User.query.filter_by(username=request.json['username']).first()
    except Exception as e:
        return jsonify(error='Could not authenticate.'), 401
    if user is None:
        return jsonify(error='Not registered.'), 401

    # Valid password
    if (user and not compare_digest(
            user.password, make_digest(request.json['password']))):
        return jsonify(error='Wrong credentials.'), 401

    if user and user.status == 'draft':

        emailToken = generate_token(
            user.id, timedelta(seconds=60 * 60 * 24),
            current_app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

        emailBody = EmailTemplate(
            template=current_app.config['REMINDER_EMAIL_TEMPLATE'],
            values={
                'title': current_app.config['REMINDER_EMAIL_SUBJECT'],
                'firstname': user.firstname,
                'serverUrl': current_app.config['SERVER_URL'],
                'token': emailToken
            }).render()

        sendmail(
            'no-reply@natural-solutions.eu', user.email,
            current_app.config['REMINDER_EMAIL_SUBJECT'], emailBody)

        return jsonify(error='user_draft'), 403

    token = generate_id_token(user.id)
    return jsonify(token=token.decode('utf-8'), profile=user.json())

@users.route('/api/users/<email>/password/recover', methods=['GET'])
def recover(email):
    try:
        user = User.query.filter_by(username=email).first()
    except Exception as e:
        return jsonify(error='Could not verify.'), 401
    if user is None:
        return jsonify(error='Not registered.'), 401
    else:
        new_pass = id_generator()
        User.query. \
            filter(User.id == user.id). \
            update({User.password:make_digest(new_pass)})
        db.session.commit()
        emailBody = EmailTemplate(
            template=current_app.config['RECOVER_PASSWORD_TEMPLATE'],
            values={
                'title': current_app.config['REMINDER_EMAIL_SUBJECT'],
                'firstname': user.firstname,
                'password': new_pass,
                'serverUrl': current_app.config['SERVER_URL']
            }).render()

        sendmail(
            'no-reply@natural-solutions.eu', user.email,
            current_app.config['REMINDER_EMAIL_SUBJECT'], emailBody)
        return jsonify(new_pass)

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
