from flask import Blueprint

from . import routes, login, me, permit, dive


api = Blueprint('api', __name__)


def init_app(app):
    app.register_blueprint(routes.users)
    app.register_blueprint(login.login)
    app.register_blueprint(me.me)
    app.register_blueprint(permit.permits)
    permit.init_app(app)
    app.register_blueprint(dive.dives)
