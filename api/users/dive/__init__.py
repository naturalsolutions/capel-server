from datetime import datetime
from typing import Mapping, Sequence
from flask import (Blueprint, jsonify, request, Response)
from sqlalchemy import func, cast
import geoalchemy2

from model import (
    db, Boat, Weather, DiveSite, TypeDive, DiveTypeDive, Dive, DiveBoat)
from auth import authenticate


dives = Blueprint('dives', __name__)

@dives.route('/api/users/dives', methods=['GET'])
@authenticate
def get_dives(reqUser):
    dives = reqUser.dives.all()
    diveJsn = []
    for dive in dives:
        diveJsn.append(dive.toJSON())
    return jsonify(diveJsn)

@dives.route('/api/users/<int:id>/dive', methods=['POST'])
@authenticate
def post_dive(reqUser=None, id=id) -> Response:
    payload = request.get_json()

    # TODO: dive structure

    dive_site = extract_site(payload)
    db.session.add(dive_site)
    db.session.commit()

    weather = extract_weather(payload)
    db.session.add(weather)
    db.session.commit()

    dive = extract_dive(id, dive_site, weather, payload)
    db.session.add(dive)
    db.session.commit()

    divetypedives = extract_dive_types(dive, payload)
    db.session.add_all(divetypedives)
    db.session.commit()

    boats = extract_boats(id, dive, payload)
    db.session.add_all(boats)
    db.session.commit()

    return jsonify('success'), 200


def extract_site(payload) -> DiveSite:
    if payload['referenced'] != 'notreferenced':
        dive_site = DiveSite.query.filter_by(referenced=payload['referenced'])\
                                  .first()
    else:
        dive_site = DiveSite(
            referenced=payload['referenced'],
            geom=db.session.query(
                func.ST_Expand(cast(
                    func.ST_GeogFromText(
                        f"POINT({str(payload['latlng']['lng'])} {str(payload['latlng']['lat'])})"),  # noqa
                geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326)), 1)).one())  # noqa
    return dive_site


def extract_weather(payload: Mapping) -> Weather:
    return Weather(**{p: payload[p] for p in [
        'sky', 'seaState', 'wind', 'water_temperature',
        'wind_temperature', 'visibility'
    ]})


def extract_dive(id: int, dive_site: DiveSite, weather: Weather,
                 payload: Mapping) -> Dive:
    return Dive(
        divingDate=payload['divingDate'],
        times=[[
            datetime.strptime(t['startTime'], '%H:%M').time(),
            datetime.strptime(t['endTime'], '%H:%M').time()
        ] for t in payload['times']],
        user_id=id,
        divesite_id=dive_site.id,
        weather_id=weather.id)


def extract_dive_types(dive: Dive, payload: Mapping) -> Sequence[DiveTypeDive]:
    return [
        DiveTypeDive(
            divetype_id=TypeDive.query.filter_by(name=d['name_mat'])
                                      .first().id,
            dive_id=dive.id,
            nbrDivers=d['nbrDivers'])
        for d in payload['divetypes']
        if d['name']]


def extract_boats(id: int, dive: Dive, payload: Mapping) -> Sequence[DiveBoat]:
    return [
        DiveBoat(
            dive_id=dive.id,
            boat_id=Boat.query.filter(
                Boat.user_id == id, Boat.name == boat['boat']).first().id)
        for boat in payload['boats']]
