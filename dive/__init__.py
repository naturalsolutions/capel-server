from datetime import datetime
from flask import (Blueprint, jsonify, request)  # , current_app, json)
from sqlalchemy import func, cast
import geoalchemy2

from auth import authenticate
from model import (
    db, Boat, Weather, DiveSite, TypeDive, DiveTypeDive, Dive, DiveBoat)


dives = Blueprint('dives', __name__)


@dives.route('/api/users/<int:id>/dive', methods=['POST'])
@authenticate
def postDive(reqUser=None, id=id):
    dive = request.get_json()
    # TODO: structure
    if dive['referenced'] != 'notreferenced':
        divesite = DiveSite.query.filter_by(referenced=dive['referenced'])\
                                 .first()
    else:
        divesite = DiveSite(
            referenced=dive['referenced'],
            geom=db.session.query(
                func.ST_Expand(cast(
                    func.ST_GeogFromText(
                        f"POINT({str(dive['latlng']['lng'])} {str(dive['latlng']['lat'])})"),  # noqa
                    geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326)), 1)).one())  # noqa
    # current_app.logger.debug(json.dumps(divesite, indent=4, sort_keys=True, default=str))  # noqa
    db.session.add(divesite)
    db.session.commit()

    weather = Weather(
        **{p: dive[p] for p in [
            'sky', 'seaState', 'wind', 'water_temperature',
            'wind_temperature', 'visibility'
        ]}
    )
    db.session.add(weather)
    db.session.commit()
    # current_app.logger.debug(json.dumps(weather, indent=4, sort_keys=True, default=str))  # noqa

    dive_occ = Dive(
        divingDate=dive['divingDate'],
        times=[[
            datetime.strptime(t['startTime'], '%H:%M').time(),
            datetime.strptime(t['endTime'], '%H:%M').time()
        ] for t in dive['times']],
        user_id=id,
        divesite_id=divesite.id,
        weather_id=weather.id)
    db.session.add(dive_occ)
    db.session.commit()

    divetypedives = [
        DiveTypeDive(
            divetype_id=TypeDive.query.filter_by(name=d['name_mat'])
                                      .first().id,
            dive_id=dive_occ.id,
            nbrDivers=d['nbrDivers'])
        for d in dive['divetypes']
        if d['name']]
    db.session.add_all(divetypedives)
    db.session.commit()
    # current_app.logger.debug(json.dumps(divetypedives, indent=4, sort_keys=True, default=str))  # noqa

    boats = [
        DiveBoat(
            dive_id=dive_occ.id,
            boat_id=Boat.query.filter(
                Boat.user_id == id, Boat.name == boat['boat']).first().id)
        for boat in dive['boats']]
    db.session.add_all(boats)
    db.session.commit()
    # current_app.logger.debug(json.dumps([boat.toJSON() for boat in boats], indent=4, sort_keys=True, default=str))  # noqa

    return jsonify('success'), 200
