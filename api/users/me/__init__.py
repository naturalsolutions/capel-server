import sys
from traceback import format_exception_only
from flask import (Blueprint, jsonify, request, current_app)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from model import db, User, Boat, unique_constraint_key, not_null_constraint_key, unique_constraint_error, not_null_constraint_error
from auth import authenticate

me = Blueprint('me', __name__)


@me.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.json()
    return jsonify(reqUser)


""" @me.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    userPatch = request.get_json()
    User.query.filter_by(id=reqUser.id).update(userPatch)
    db.session.commit()
    user = User.query.filter_by(id=reqUser.id).first()
    return jsonify(user.json()) """

@me.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    #userPatch = {key: value for key, value in request.get_json().items() if value != ''}
    userPatch = {}
    for key, value in request.get_json().items():
        if value != '':
            userPatch[key] = value

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
            #TODO factorize
            except (IntegrityError, Exception) as e:
                db.session.rollback()
                err_type, err_value, tb = sys.exc_info()
                current_app.logger.warn(
                    ''.join(format_exception_only(err_type, err_value)))
                err_orig = str(getattr(e, 'orig', 'register error'))
                errors = []

                if err_orig.find('violates unique constraint') > -1:
                    errorValue = unique_constraint_error(err_orig)
                    err_value.index = i
                    errors.append(errorValue)

                elif err_orig.find('violates not-null constraint') > -1:
                    errorValue = not_null_constraint_error(str(e))
                    err_value.index = i
                    errors.append(errorValue)

                return jsonify(error={'name': 'invalid_model', 'errors': errors}), 400
    
    try:
        User.query.filter_by(id=reqUser.id).update(userPatch)
        db.session.commit()
    #TODO factorize
    except (IntegrityError, Exception) as e:
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
    user = User.query.filter_by(id=reqUser.id).first()

    return jsonify(user.json())

#TODO facorize with users.validate_boats
def validate_boats(boats):
    errors = []

    for i, boat in enumerate(boats):
        if boat in (None, ''):
            errors.append(
                {'name': 'invalid_format', 'key': f'boats{i}'})
            continue

        elif boat.get('name') in (None, ''):
            errors.append({
                'table': 'boats',
                'column': 'name',
                'value': boat.get('name'),
                'name': 'missing_attribute',
                'index': i
            })

        elif boat.get('matriculation') in (None, ''):
            errors.append({
                'table': 'boats',
                'column': 'matriculation',
                'value': boat.get('matriculation'),
                'name': 'missing_attribute',
                'index': i
            })

    if len(errors) >= 0:
        return {'errors': errors}
    return True