from flask import Blueprint, jsonify

from model import TypeDive
from . import users


api = Blueprint('api', __name__)


def init_app(app):
    users.init_app(app)


@api.route('/api/dives/typedives')
def getTypeDives():
    typeDives = TypeDive.query.all()
    typeDivesJsn = []
    for typeDive in typeDives:
        typeDivesJsn.append(typeDive.json())
    return jsonify(typeDivesJsn)
