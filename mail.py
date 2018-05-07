from flask import (Blueprint, jsonify, current_app, redirect)
import jwt
import sendgrid
from sendgrid.helpers.mail import (Email, Content, Mail)

from auth import generate_id_token
from model import db, User

mail = Blueprint('mail', __name__)


class EmailTemplate(object):

    def __init__(self, template='', values={}):
        self.template = template
        self.values = values

    def render(self):
        content = ''
        with open(self.template, 'r') as t:
            content = t.read()
            for k, v in self.values.items():
                content = content.replace('{{{{{}}}}}'.format(k), v)
        return str(content)


def sendmail(from_email, to_email, subject, content):
    sg = sendgrid.SendGridAPIClient(
        apikey=current_app.config['SENDGRID_API_KEY'])
    from_email = Email(from_email)
    to_email = Email(to_email)
    subject = str(subject)
    content = Content('text/html', content)
    mail = Mail(from_email, subject, to_email, content)
    sg.client.mail.send.post(request_body=mail.get())


@mail.route('/emailconfirm/<emailtoken>')
def emailconfirm(emailtoken):
    if emailtoken is None:
        return jsonify(code=401), 401

    payload = jwt.decode(
        emailtoken,
        key=current_app.config['JWTSECRET'] + b'_emailconfirm',
        algorithm='HS256')
    user = User.query.filter_by(id=payload['id']).first()
    if user is None:
        return jsonify(error=payload), 403

    user.status = 'enabled'
    db.session.commit()
    token = generate_id_token(user.id).decode('utf-8')
    return redirect(
        '{webappUrl}?flash_message=email_confirm_success&token={token}'
        .format(webappUrl=current_app.config['WEBAPP_URL'], token=token),
        code=302)
