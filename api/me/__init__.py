from flask import (Blueprint, jsonify, request)

from model import db, User
from auth import authenticate

me = Blueprint('me', __name__)


@me.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)


@me.route('/api/users/me', methods=['PATCH'])
@authenticate
def patchMe(reqUser):
    userPatch = request.get_json()
    User.query.filter_by(id=reqUser.id).update(userPatch)
    db.session.commit()
    user = User.query.filter_by(id=reqUser.id).first()
    return jsonify(user.toJSON())
