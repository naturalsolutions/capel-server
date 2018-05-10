from flask import Blueprint

from . import login, users, me, permit, dive


api = Blueprint('api', __name__)


def init_app(app):
    app.register_blueprint(login.login_bp)
    app.register_blueprint(users.users)
    app.register_blueprint(me.me)
    app.register_blueprint(permit.permits)
    permit.init_app(app)
    app.register_blueprint(dive.dives)
