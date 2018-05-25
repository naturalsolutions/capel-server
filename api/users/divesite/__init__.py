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

