import os
from datetime import timedelta



SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWTSECRET = b'SUPER_SECRET'
JWT_AUTH_TYPE = 'Bearer'
JWT_ID_TK_EXP = timedelta(seconds=86400)
VALID_PWD_MIN_LEN = 6
PERMIT_TEMPLATE = 'assets/reglement_2017.pdf'
PERMITS_DIR = 'permits'
SENDGRID_API_KEY = os.environ.get('SENDGRID_KEY')
WEBAPP_URL = 'http://149.202.44.29/capel-client'
SERVER_URL = 'https://capel-beta.herokuapp.com/'


WEBAPP_URL = 'http://149.202.44.29/capel-client'
SERVER_URL = 'https://capel-beta.herokuapp.com/'

WELCOME_EMAIL_SUBJECT = 'Bienvenue sur CAPEL'
WELCOME_EMAIL_TEMPLATE = 'assets/welcome_email_template.html'
REMINDER_EMAIL_SUBJECT = 'Valider votre compte'
REMINDER_EMAIL_TEMPLATE = WELCOME_EMAIL_TEMPLATE

PERMIT_TEMPLATE = 'assets/reglement_2017.pdf'
PERMITS_DIR = 'permits'

VALID_PWD_MIN_LEN = 6
VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'


