import sys
from traceback import format_exception_only
from datetime import datetime
from typing import Mapping, Sequence
from flask import (Blueprint, jsonify, request, Response, current_app)
import traceback
from model import (
    db, User, Boat, Weather, DiveSite, TypeDive, DiveTypeDive, Dive)
from auth import authenticate, authenticateAdmin
from sqlalchemy import func

WEATHER_DATA_MAP = {
    'sky': 'sky',
    'sea': 'seaState',
    'wind': 'wind',
    'water_temperature': 'water_temperature',
    'wind_temperature': 'wind_temperature',
    'visibility': 'visibility'
}

dives = Blueprint('dives', __name__)

@dives.route('/api/dives', methods=['GET'])
@authenticateAdmin
def get_adm_dives(reqUser):
        return jsonify([dive.json() for dive in Dive.query.all()])

@dives.route('/api/dives/count', methods=['GET'])
@authenticate
def get_count_dives(reqUser):
    data = db.session.query(func.count(Dive.id)).scalar()
    return  jsonify(data)

@dives.route('/api/dives/count/bydate', methods=['GET'])
@authenticateAdmin
def get_count_filtred_dives(reqUser):
    data = db.session.query(Dive.date, func.count(Dive.date)).group_by(Dive.date).order_by(Dive.date).all()
    return  jsonify(data)
"""
@dives.route('/api/dives/count/bysite', methods=['GET'])
@authenticateAdmin
def get_count_filtred_dives_by_sites(reqUser):
    data = db.session.query(Dive.date, Dive.dive_site.name, func.count(Dive.dive_site.name)).group_by(Dive.dive_site.name).order_by(Dive.dive_site.name).all()
    return  jsonify(data)
"""

@dives.route('/api/users/dives', methods=['GET'])
@authenticate
def get_dives(reqUser):
    return jsonify([dive.json() for dive in reqUser.dives.order_by((Dive.date)).all()])

@dives.route('/api/users/dives/<int:id>', methods=['DELETE'])
@authenticate
def delete_dive(reqUser, id=id):
    try:
        dive = Dive.query.filter_by(id=id).delete()
        db.session.commit()
        if dive:
            return jsonify('dive has been deleted')
        else:
            return jsonify('problem')
    except Exception as e:
        traceback.print_exc()



@dives.route('/api/users/dives/<int:id>', methods=['GET'])
def get_dive(id=id):
    dive = Dive.query.get(id)
    if dive:
        return jsonify(dive.json())
    else:
        return 'error not found'

@dives.route('/api/users/<int:id>/dives', methods=['POST'])
@authenticate
def post_dive(reqUser=None, id=id) -> Response:
    try:
        payload = request.get_json()
        # current_app.logger.debug(json.dumps(payload, indent=4))

        weather = extract_weather(payload)
        db.session.add(weather)
        db.session.commit()

        dive_site = extract_site(payload)


        dive = extract_dive(dive_site, weather, id, payload)
        db.session.add(dive)
        db.session.commit()

        divetypedives = extract_dive_types_dive(dive, payload)
        db.session.add_all(divetypedives)
        db.session.commit()

        return jsonify('success'), 200

    except Exception:
        db.session.rollback()
        err_type, err_value, tb = sys.exc_info()
        current_app.logger.warn(
            ''.join(format_exception_only(err_type, err_value)))
        raise

        if err_type == 'TypeError':
            return jsonify(error='Invalid JSON.'), 400

        return jsonify(error='Dive registration error.'), 400


def extract_site(payload) -> DiveSite:
    # if payload['referenced'] == 'referenced':
    #     dive_site = DiveSite.query.filter_by(referenced=payload['referenced'])\  # noqa
    #                               .first()
    # else:
    dive_site = DiveSite.query.get(payload['divesite_id'])
    return dive_site


def extract_weather(payload: Mapping) -> Weather:
    return Weather(**{k: payload[v] for k, v in WEATHER_DATA_MAP.items()})


def extract_dive(
        dive_site: DiveSite,
        weather: Weather,
        uid: int,
        payload: Mapping) -> Dive:
    # current_app.logger.debug(dive_site.id)
    return Dive(
        user_id=uid,
        site_id=dive_site.id,
        date=payload['divingDate'],
        comment=payload['comment'],
        times=[[
            datetime.strptime(t['startTime'], '%H:%M').time(),
            datetime.strptime(t['endTime'], '%H:%M').time()
        ] for t in payload['times']],
        weather_id=weather.id,
        #latitude=payload['latlng']['lat'],
        #longitude=payload['latlng']['lng'],
        boats=extract_dive_boats(uid, payload),
        shop=User.query.get(payload['structure']['id']) if payload['isWithStructure'] else None  # noqa
    )


def extract_dive_boats(uid: int, payload: Mapping) -> Sequence[Boat]:
    # current_app.logger.debug(payload['boats'])
    result = [
        # User.query.filter(User.boats.name == boat['boat']).first()
        Boat.query.filter(
            Boat.user_id == uid, Boat.name == boat['boat']).first()
        for boat in payload['boats'] if len(payload['boats']) > 0]
    # current_app.logger.debug(result)
    return result


def extract_dive_types(payload: Mapping) -> Sequence[DiveTypeDive]:
    # current_app.logger.debug(json.dumps(payload['divetypes'], indent=4))
    return [
        TypeDive.query.filter_by(name=d['nameMat']).first()
        for d in payload['divetypes'] if d['name']]


def extract_dive_types_dive(
        dive: Dive,
        payload: Mapping) -> Sequence[DiveTypeDive]:
    # current_app.logger.debug(json.dumps(payload['divetypes'], indent=4))
    return [
        DiveTypeDive(
            divetype_id=TypeDive.query.filter_by(name=d['nameMat']).first().id,
            dive_id=dive.id,
            divers=d['nbrDivers'])
        for d in payload['divetypes']
        if d['name']]
