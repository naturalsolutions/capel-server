from flask import (Blueprint, jsonify, current_app)

from auth import authenticate
from model import db, User, Boat, Weather, Dive, DiveTypeDive


dives = Blueprint('dives', __name__)


@dives.route('/api/users/<int:id>/dive', methods=['POST'])
@authenticate
def postDive(reqUser=None, id=id):
    # {
    #     "divingDate":"2018-05-05T22:00:00.000Z",
    #     "referenced":"referenced"|"notreferenced",
    #     "times":[
    #         {"startTime":"09:30"|'',"endTime":"10:00"},
    #         {"startTime":"14:00","endTime":"15:00"}
    #     ],
    #     "divetypes":[
    #         {"name":false,"name_mat":"Baptême","nbrDivers":""},
    #         {"name":false,"name_mat":"Exploration","nbrDivers":""},
    #         {"name":false,"name_mat":"Technique","nbrDivers":""},
    #         {"name":false,"name_mat":"Randinnée palmeée","nbrDivers":""},
    #         {"name":true,"name_mat":"Apneée","nbrDivers":"4"}
    #     ],
    #     "boats":[{"boat":"Le Gégène"}],
    #     "wind":5,
    #     "water_temperature":"18",
    #     "wind_temperature":"23",
    #     "visibility":"10000",
    #     "sky":"weather_soleil",
    #     "seaState":"weather_mouvemente",
    #     "structure":"",
    #     "isWithStructure":false,
    #     "latlng":{"lat":43.02874525134882, "lng":6.4139556884765625}
    # }

    # maybe (structure, latlng, referenced, divetypes.id, times)

    return jsonify('Hello '), 200
