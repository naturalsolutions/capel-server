from flask import (Blueprint, jsonify, request)

from model import db, DiveSite
from auth import authenticate

divesite = Blueprint('divesite', __name__)


@divesite.route('/api/users/divesites')
def getDiveSites():
    return jsonify([diveSite.json() for diveSite in DiveSite.all_sites()])

@divesite.route('/api/users/divehearts')
def getDiveHearts():
    return jsonify([diveSite.json() for diveSite in DiveSite.all_hearts()])

@divesite.route('/api/users/divehearts/checkpoint', methods=['POST'])
def get_hearts():
    payload = request.get_json()
    return jsonify([diveSite.cusJson() for diveSite in DiveSite.getHeartsByPoint(str(payload['lat']), str(payload['lng']))])

@divesite.route('/api/users/divesite/save', methods=['POST'])
@authenticate
def save(reqUser):
        payload = request.get_json()
        diveSite = DiveSite(**payload)
        diveSite.user_id = reqUser.id
        db.session.add(diveSite)
        db.session.commit()
        return jsonify(diveSite.cusJson())

@divesite.route('/api/users/owndivesites', methods=['GET'])
@authenticate
def getUserDiveSites(reqUser):
        #payload = request.get_json()
        return jsonify( [diveSite.cusJson() for diveSite in DiveSite.getOwnUserSite(reqUser)])

