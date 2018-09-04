from flask import (Blueprint, jsonify, request)

from model import db, DiveSite
from auth import authenticate
from sqlalchemy import func
divesites = Blueprint('divesites', __name__)

@divesites.route('/api/divesites/count', methods=['GET'])
@authenticate
def get_count_divesites(reqUser):
    data = db.session.query(func.count(DiveSite.id)).scalar()
    return  jsonify(data)

@divesites.route('/api/users/divesites')
def getDiveSites():
    return jsonify([diveSite.json() for diveSite in DiveSite.all_sites()])

@divesites.route('/api/users/divehearts')
def getDiveHearts():
    return jsonify([diveSite.json() for diveSite in DiveSite.all_hearts()])

@divesites.route('/api/users/divehearts/checkpoint', methods=['POST'])
def get_hearts():
    payload = request.get_json()
    return jsonify([diveSite.cusJson() for diveSite in DiveSite.getHeartsByPoint(str(payload['lat']), str(payload['lng']))])

@divesites.route('/api/users/divesite/save', methods=['POST'])
@authenticate
def save(reqUser):
        payload = request.get_json()
        diveSite = DiveSite(**payload)
        diveSite.user_id = reqUser.id
        db.session.add(diveSite)
        db.session.commit()
        return jsonify(diveSite.cusJson())

@divesites.route('/api/users/owndivesites', methods=['GET'])
@authenticate
def getUserDiveSites(reqUser):
        return jsonify([diveSite.cusJson() for diveSite in DiveSite.getOwnUserSite(reqUser)])

