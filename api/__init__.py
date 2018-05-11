from flask import Blueprint

from . import users


api = Blueprint('api', __name__)


def init_app(app):
    users.init_app(app)
