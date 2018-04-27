from datetime import timedelta
try:
    from dba import DATABASE_URL, SENDGRID_KEY
except Exception:
    DATABASE_URL = f'postgresql://postgres@localhost/capel'
    SENDGRID_KEY = 'Please fill in your sendgrid api key.'  # TODO: raise

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWTSECRET = b'SUPER_SECRET'
JWT_AUTH_TYPE = 'Bearer'
JWT_ID_TK_EXP = timedelta(seconds=300)
VALID_PWD_MIN_LEN = 6
VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
PERMIT_TEMPLATE = 'assets/reglement_2017.pdf'
PERMITS_DIR = 'permits'
SENDGRID_API_KEY = SENDGRID_KEY
WEBAPP_URL = 'htt://localhost:4200'
SERVER_URL = 'https://capel-beta.herokuapp.com/'
