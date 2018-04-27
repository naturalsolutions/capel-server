#!/usr/bin/python3

import os
import sys
import datetime
import re
from traceback import format_exception_only
from functools import wraps
from flask import (Flask, jsonify, request, make_response, redirect,
                   Response, send_from_directory)
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_cors import CORS
import jwt
import hmac
import sendgrid
from sendgrid.helpers.mail import (Email, Content, Mail)
from datetime import timedelta

from email_template import EmailTemplate


VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
DUPLICATE_KEY_ERROR_REGEX = r'DETAIL:\s+Key \((?P<duplicate_key>.*)\)=\(.*\) already exists.'  # noqa
WELCOME_EMAIL_SUBJECT = 'Bienvenue sur CAPEL'
WELCOME_EMAIL_TEMPLATE = 'assets/welcome_email_template.html'
REMINDER_EMAIL_SUBJECT = 'Valider votre compte'
REMINDER_EMAIL_TEMPLATE = WELCOME_EMAIL_TEMPLATE

app = Flask(__name__)
CORS(app)
app.config.from_object('app_conf')
if os.environ.get('CAPEL_CONF', None):
    app.config.from_envvar('CAPEL_CONF')

from models import db, User, Boat  # noqa
# db.init(app)
migrate = Migrate(app, db)


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
        if request.headers.get('Authorization') is None:
            return f(None, *args, **kwargs)
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


@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)


@app.route("/")
def hello():
    return 'hello capel-server !'


@app.route('/emailconfirm/<emailtoken>')
def emailconfirm(emailtoken):
    if emailtoken is None:
        return jsonify(code=401), 401

    payload = jwt.decode(
        emailtoken,
        key=app.config['JWTSECRET'] + b'_emailconfirm',
        algorithm='HS256')
    user = User.query.filter_by(id=payload['id']).first()

    if user is None:
        return jsonify(error=payload), 403

    user.status = 'enabled'
    db.session.commit()

    token = generate_id_token(user.id).decode('utf-8')

    return redirect('{webappUrl}#/?flash_message=email_confirm_success&token={token}'.format(webappUrl=app.config['WEBAPP_URL'], token=token), code=302)  # noqa


@app.route('/api/users/login', methods=['POST'])
def login():
    user = None

    # Required fields
    if (request.json is None or
        request.json.get('password') in (None, '') or
            request.json.get('username') in (None, '')):
        return make_response('Could not authenticate.', 401)

    # Registered user
    try:
        user = User.query.filter_by(username=request.json['username']).first()
    except Exception as e:
        return make_response(
            'Could not authenticate bla.', 401)
    if user is None:
        return jsonify(error='Wrong credentials.'), 401
    # Valid password
    if (user and not hmac.compare_digest(
            user.password, make_digest(request.json['password']))):
        return jsonify(error='Wrong credentials.'), 401

    if user and user.status == 'draft':
        emailToken = generate_token(
            user.id,
            timedelta(seconds=60 * 60 * 24),
            app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

        emailBody = EmailTemplate(
            template=REMINDER_EMAIL_TEMPLATE,
            values={
                'title': REMINDER_EMAIL_SUBJECT,
                'firstname': user.firstname,
                'serverUrl': app.config['SERVER_URL'],
                'token': emailToken
            }).render()

        sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
        from_email = Email('no-reply@natural-solutions.eu')
        to_email = Email(user.email)
        subject = REMINDER_EMAIL_SUBJECT
        content = Content("text/html", emailBody)
        mail = Mail(from_email, subject, to_email, content)
        sg.client.mail.send.post(request_body=mail.get())
        return jsonify(error='user_draft'), 403

    token = generate_id_token(user.id)
    return jsonify(token=token.decode('utf-8'), profile=user.toJSON())


@app.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)


@app.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    userPatch = request.get_json()
    User.query.filter_by(id=reqUser.id).update(userPatch)
    db.session.commit()
    user = User.query.filter_by(id=reqUser.id).first()
    return jsonify(user.toJSON())


@app.route('/api/users', methods=['POST'])
def postUsers():
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
        if boats:
            if not isinstance(boats, list) or not validate_boats(boats):
                return jsonify(
                    error={'name': 'invalid_model',
                           'errors': [{'name': 'invalid_format',
                                       'key': 'boats'}]}), 400

            user['boats'] = [Boat(**boat) for boat in boats]

        user['status'] = 'draft'
        user['createdAt'] = datetime.datetime.utcnow()
        user['password'] = make_digest(user['password'])
        user = User(**user)

    except Exception as e:
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))

        if err_type == 'TypeError':
            return jsonify(error='Invalid JSON.'), 400

        return jsonify(error='Empty or malformed required filed user.'), 400

    try:

        db.session.add(user)
        db.session.commit()
    except (IntegrityError, Exception) as e:
        db.session.rollback()
        err_type, err_value, tb = sys.exc_info()
        app.logger.warn(''.join(format_exception_only(err_type, err_value)))
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
        user.id, timedelta(seconds=60 * 60 * 24),
        app.config['JWTSECRET'] + b'_emailconfirm').decode('utf-8')

    emailBody = EmailTemplate(
        template=WELCOME_EMAIL_TEMPLATE,
        values={
            'title': WELCOME_EMAIL_SUBJECT,
            'firstname': user.firstname,
            'serverUrl': app.config['SERVER_URL'],
            'token': emailToken
        }).render()

    sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
    from_email = Email('no-reply@natural-solutions.eu')
    to_email = Email(user.email)
    subject = WELCOME_EMAIL_SUBJECT
    content = Content('text/html', emailBody)
    mail = Mail(from_email, subject, to_email, content)
    sg.client.mail.send.post(request_body=mail.get())

    return jsonify(user.toJSON())


@app.route('/api/users', methods=['GET'])
@authenticateOrNot
def getUsers(reqUser):
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


@app.route('/api/users/<int:id>/permit.pdf', methods=['GET'])
@authenticate
def getPermit(reqUser, id):

    os.makedirs(app.config['PERMITS_DIR'], exist_ok=True)

    response = None
    user = User.query.filter_by(id=id).first_or_404()
    if user is not None:
        now = datetime.datetime.utcnow()
        f = '/'.join([
            app.config['PERMITS_DIR'],
            '_'.join(['permit', 'capel',
                      str(now.year), str(user.firstname),
                      str(user.id)]) + '.pdf'])
        if not os.path.isfile(f):
            from pdfgen import Applicant, Permit

            applicant = Applicant([
                (user.firstname + ' ' + user.lastname, 156, 122),
                (user.phone, 135, 105),
                (user.email, 100, 88)])

            boats = user.boats.all()
            if boats not in (None, []):
                boats = ([', '.join([
                    ' '.join([boat.name, boat.matriculation])
                    for boat in user.boats])],
                    180, 70)
            else:
                boats = ('Aucun', 180, 70)

            permit = Permit(
                applicant,
                boat=boats,
                template=app.config['PERMIT_TEMPLATE'],
                site='Parc National de Port-Cros',
                save_path=f)
            permit.save()

        try:
            with open(f, 'rb') as pdf:
                response = Response(pdf.read())
                response.mimetype = 'application/pdf'
                response.headers['Content-Disposition'] = (
                    'attachment; filename={}'.format(os.path.basename(f)))
                return response
        except Exception as e:
            err_type, err_value, tb = sys.exc_info()
            app.logger.warn(
                ''.join(format_exception_only(err_type, err_value)))
            return '500 error', 500


def make_digest(msg):
    return hmac.new(
        app.config['JWTSECRET'],
        msg=msg.encode(),
        digestmod='sha256').hexdigest()


def generate_id_token(id):
    return generate_token(
        id, app.config['JWT_ID_TK_EXP'], app.config['JWTSECRET'])


def generate_token(id, duration, secret):
    utc_now = datetime.datetime.utcnow()
    return jwt.encode(
        {'id': id, 'exp': utc_now + duration}, secret, algorithm='HS256')


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

    if len(errors) >= 0:
        return {'errors': errors}

    return True


def validate_boats(boats):
    errors = []

    for i, boat in enumerate(boats):
        if boat in (None, ''):
            errors.append({'name': 'invalid_format', 'key': boat[i].name})
            continue

        if boat.get('name') in (None, ''):
            errors.append({'name': 'invalid_format', 'key': boat[i].name})

        if boat.get('matriculation') in (None, ''):
            errors.append({'name': 'invalid_format',
                           'key': boat[i].matriculation})

    if len(errors) >= 0:
        return {'errors': errors}
    return True


def not_null_constraint_key(error):
    return error.split('violates not-null constraint')[0] \
                .split('column')[1].strip().replace('"', '')


def unique_constraint_key(error):
    m = re.search(DUPLICATE_KEY_ERROR_REGEX, error)
    return m.group('duplicate_key')
