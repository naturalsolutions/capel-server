import sys
from traceback import format_exception_only
from datetime import datetime
from typing import Mapping, Sequence
from flask import (Blueprint, jsonify, request, Response, current_app)
from sqlalchemy import func, cast
import geoalchemy2

from model import (
    db, User, Boat, Weather, DiveSite,
    TypeDive, DiveTypeDive, Dive)
from auth import authenticate


dives = Blueprint('dives', __name__)


@dives.route('/api/users/dives', methods=['GET'])
@authenticate
def get_dives(reqUser):
    dives = reqUser.dives.all()
    diveJsn = []
    for dive in dives:
        diveJsn.append(dive.json())
    return jsonify(diveJsn)


@dives.route('/api/users/<int:id>/dives', methods=['POST'])
@authenticate
def post_dive(reqUser=None, id=id) -> Response:
    try:
        payload = request.get_json()
        dive_site = extract_site(payload)
        dive = extract_dive(dive_site, id, payload)
        db.session.add(dive)
        db.session.commit()

        divetypedives = extract_dive_types(dive, payload)
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
    if payload['referenced'] == 'referenced':
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
        'sky', 'sea', 'wind', 'water_temperature',
        'wind', 'visibility'
    ]})


def extract_dive(
        dive_site: DiveSite,
        uid: int,
        payload: Mapping) -> Dive:
    return Dive(
        user_id=uid,
        dive_site_id=dive_site.id,
        divingDate=payload['divingDate'],
        times=[[
            datetime.strptime(t['startTime'], '%H:%M').time(),
            datetime.strptime(t['endTime'], '%H:%M').time()
        ] for t in payload['times']],
        weather=Weather(**{p: payload[p] for p in [
            'sky', 'sea', 'wind', 'water_temperature',
            'wind', 'visibility'
        ]}),
        latitude=payload['latlng']['lat'],
        longitude=payload['latlng']['lng'],
        boats=[
            Boat.query.filter(
                Boat.user_id == uid, Boat.name == boat['boat']).first().id
            for boat in payload['boats']],
        shop_id=User.query.get(payload['structure']['id']) if payload['isWithStructure'] else None  # noqa
    )


def extract_dive_types(dive: Dive, payload: Mapping) -> Sequence[DiveTypeDive]:
    return [
        DiveTypeDive(
            divetype_id=TypeDive.query.filter_by(name=d['nameMat']).first().id,
            dive_id=dive.id,
            divers=d['divers'])
        for d in payload['divetypes']
        if d['name']]
