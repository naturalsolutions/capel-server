from credentials import dbcredentials as dba
from datetime import timedelta

SQLALCHEMY_DATABASE_URI = f'postgresql://{dba}localhost/capel'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWTSECRET = b'abcdef'
JWT_AUTH_TYPE = 'Bearer'
JWT_ID_TK_EXP = timedelta(seconds=30)
VALID_PWD_MIN_LEN = 6
VALID_EMAIL_REGEX = r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
PERMIT_TEMPLATE = 'assets/reglement_2017_de_plongee_sous_marine_dans_les_coeurs_marins_du_parc_national.pdf'  # noqa
PERMITS_DIR = 'permits'
SENDGRID_API_KEY = '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'
WEBAPP_URL = 'htt://localhost:4200'
SERVER_URL = 'http://vps515776.ovh.net/capel'
