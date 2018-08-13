from flask import (Blueprint, Response, current_app, request, jsonify)
from model import Boat
from auth import ( authenticateAdmin)
from sqlalchemy import func, desc

boats = Blueprint('boats', __name__)



@boats.route('/api/boats', methods=['GET'])
@authenticateAdmin
def get_boats(reqUser):
    boats = Boat.query.\
        order_by(desc(Boat.id)). \
        all()
    return jsonify([boat.json() for boat in boats])