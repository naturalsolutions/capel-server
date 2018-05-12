import sys
import datetime
from traceback import format_exception_only
import re
from flask import (Blueprint, jsonify, request, current_app)
from sqlalchemy.exc import IntegrityError

from mail import EmailTemplate, sendmail


from model import (db, User, Boat,
                   unique_constraint_key, not_null_constraint_key)
from auth import (make_digest, generate_token, authenticate)


users = Blueprint('users', __name__)


@users.route('/api/users', methods=['POST'])
def post_users():
    # Signup/Register
    try:
        payload = request.get_json()
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

        return jsonify(error='Empty or malformed required filed user.'), 400

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
        template=current_app.WELCOME_EMAIL_TEMPLATE,
        values={
            'title': current_app.WELCOME_EMAIL_SUBJECT,
            'firstname': user.firstname,
            'serverUrl': current_app.config['SERVER_URL'],
            'token': emailToken
        }).render()

    sendmail('no-reply@natural-solutions.eu', user.email,
             current_app.WELCOME_EMAIL_SUBJECT, emailBody)

    return jsonify(user.toJSON())


@users.route('/api/users', methods=['GET'])
# @authenticate'
# def getUsers(reqUser):
def getUsers():
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


@users.route('/api/users/boats')
@authenticate
def getBoats(reqUser):
    boats = reqUser.boats.all()
    boatJsn = []
    for boat in boats:
        boatJsn.append(boat.toJSON())
    return jsonify(boatJsn)


def users_validate_required(user):
    errors = []

    if (not user.get('category', None) or
            user.get('category') not in ('particulier', 'structure')):
        errors.append({'name': 'invalid_format', 'key': 'category'})

    if len(user['password']) < current_app.config['VALID_PWD_MIN_LEN']:
        errors.append({'name': 'invalid_format', 'key': 'password',
                       'message': 'Password length must be >= ' +
                                  current_app.config['VALID_PWD_MIN_LEN']})

    if not re.match(current_app.VALID_EMAIL_REGEX, user['email'], re.I):
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
                {'name': 'invalid_format', 'key': f'boat{i}'})
            continue

        elif boat.get('name') in (None, ''):
            errors.append({'name': 'invalid_format', 'key': boat[i].name})

        elif boat.get('matriculation') in (None, ''):
            errors.append(
                {'name': 'invalid_format', 'key': boat[i].matriculation})

    if len(errors) >= 0:
        return {'errors': errors}
    return True
