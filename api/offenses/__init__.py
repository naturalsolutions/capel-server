from flask import (Blueprint, Response, current_app, request, jsonify)
from model import Offense, db
from auth import ( authenticateAdmin)
from sqlalchemy import func, desc
from validators import( offense_validate_required )
import traceback

offenses = Blueprint('offenses', __name__)

@offenses.route('/api/offenses', methods=['GET'])
@authenticateAdmin
def get_offences(reqUser):
    offences = Offense.query.\
        order_by(desc(Offense.id)). \
        all()
    return jsonify([offence.json() for offence in offences])

@offenses.route('/api/offenses', methods=['POST'])
@authenticateAdmin
def save_offences(reqUser):
    try:
        payload = request.get_json()
    except Exception:
        return jsonify(error='Invalid JSON.')
    validation = offense_validate_required(payload)
    if validation['errors']:
        return jsonify(error={'name': 'invalid_model',
                              'errors': validation['errors']}), 400
    offense = Offense(**payload)
    oldOffense = Offense.query.filter(Offense.user_id == payload['user_id']).first()
    try:
        if(oldOffense):
            db.session.query(Offense).filter(Offense.user_id == payload['user_id']).update(payload)
        else:
            db.session.add(offense)
        db.session.commit()
        return jsonify({'name': 'success', 'errors': 'bo'}), 200
    except (Exception) as e:
        traceback.print_exc()
        db.session.rollback()
        return jsonify(error={'name': 'invalid_model', 'errors':'offence'}), 400
