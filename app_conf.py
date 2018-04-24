from datetime import timedelta

SQLALCHEMY_DATABASE_URI = 'postgres://nprxexbyoznabo:9a18f5b097e560f1bad29b559e6c4d20fff688c74cd747ff0851b28455377923@ec2-107-20-151-189.compute-1.amazonaws.com:5432/de9j10rfk0jqgi'
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
SERVER_URL = 'https://capel-beta.herokuapp.com/'
