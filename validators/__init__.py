import re
from flask import (current_app)
# TODO facorize with users.validate_boats
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


def users_validate_required(user):
    errors = []

    if (not user.get('category', None) or
            user.get('category') not in ('particulier', 'structure')):
        errors.append({
            'name': 'invalid_format',
            'key': 'category'
        })

    if len(user['password']) < current_app.config['VALID_PWD_MIN_LEN']:
        errors.append({
            'name': 'invalid_password',
            'key': 'password',
            'message': 'Password length must be >= ' +
                                  current_app.config['VALID_PWD_MIN_LEN']
        })

    if not re.match( current_app.config['VALID_EMAIL_REGEX'], user['email'], re.I ):
        errors.append({
            'table': 'users',
            'name': 'invalid_email',
            'column': 'email'
        })

    for attr in ('lastname', 'firstname', 'address', 'phone', 'city'):
        if not user.get(attr, None):
            errors.append({
                'name': 'missing_attribute',
                'table': 'users',
                'column': attr
            })

    if len(errors) >= 0:
        return {'errors': errors}

    return True


def offense_validate_required(offense):
     errors = []
     for attr in ('start_at', 'end_at', 'user_id', 'status'):
        if not offense.get(attr, None):
            errors.append({
                'name': 'missing_attribute',
                'table': 'offences',
                'column': attr
            })
     if len( errors ) >= 0:
        return {'errors': errors}

     return True
