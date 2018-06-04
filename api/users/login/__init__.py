from datetime import timedelta
from flask import (Blueprint, jsonify, request, current_app)
import string
import random
from model import (db, User)
from auth import (
    generate_token, generate_id_token, make_digest, compare_digest)
from mail import EmailTemplate, sendmail

login = Blueprint('login', __name__)


@login.route('/api/users/login', methods=['POST'])
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
@login.route('/api/users/<email>/password/recover', methods=['GET'])
def recover(email):
    try:
        print(email)
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
        print(new_pass)
        return jsonify(new_pass)



def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))