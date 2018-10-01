import os
import sys
import datetime
from typing import Mapping, Sequence
from traceback import format_exception_only
from flask import (Blueprint, Response, current_app, request, jsonify)
import traceback
from model import User, TypePermit, db, TypePermitHearts, Permit
from auth import ( authenticate, authenticateAdmin)
import base64
from pathlib import Path
from sqlalchemy import func
DATA_DIR = None
from sqlalchemy import or_, desc
from mail import EmailTemplate, sendmail
permits = Blueprint('permits', __name__)


def init_app(app):
    global DATA_DIR
    DATA_DIR = app.config['PERMITS_DIR']
    os.makedirs(DATA_DIR, exist_ok=True)

@permits.route('/api/permits/count', methods=['GET'])
@authenticateAdmin
def get_count_users(reqUser):
    data = db.session.query(func.count(Permit.id)).scalar()
    return  jsonify(data)

@permits.route('/api/users/<int:id>/permit.pdf', methods=['GET'])
def get_permit(id):
    try:
        response = None
        user = User.query.filter_by(id=id).first_or_404()
        typePermit = TypePermit.query.filter_by(status='enabled').first()
        permit_model = str(current_app.config['PERMIT_PATH']+"/"+str(typePermit.id)+".pdf")
        my_file = Path(permit_model)
        if not my_file.is_file():
            with open(permit_model, 'wb') as fout:
                fout.write(base64.decodestring((bytes(typePermit.template, 'utf-8'))))
        permit =  Permit()
        instance = db.session.query(Permit).filter_by(user_id = id, typepermit_id = typePermit.id).first()
        if  instance is None:
            permit.user_id = id
            permit.typepermit_id = typePermit.id
            db.session.add(permit)
            db.session.commit()
            emailBody = EmailTemplate(
                template=current_app.config['PERMIT_SIGNED_TEMPLATE'],
                values={
                    'title': current_app.config['PERMIT_SIGNED_SUBJECT'],
                    'firstname': user.firstname,
                    'serverUrl': current_app.config['SERVER_URL']
                }).render()

            sendmail(
                'no-reply@natural-solutions.eu', user.email,
                current_app.config['PERMIT_SIGNED_SUBJECT'], emailBody)

        if user is not None:
            now = datetime.datetime.utcnow()
            f = '/'.join([
                DATA_DIR,
                '_'.join(['Autorisation', 'PNPC',
                          str(now.year), str(user.id),str(typePermit.id)])
                + '.pdf'])
            if not os.path.isfile(f):
                from .pdfmix import Applicant, PermitView

                applicant = Applicant([
                    (user.firstname + ' ' + user.lastname, 156, 122),
                    (user.phone, 135, 105),
                    (user.email, 100, 88)])

                boats = user.boats.all()
                if boats not in (None, []):
                    boats = ([', '.join([
                        ' '.join([boat.name, boat.matriculation])
                        for boat in user.boats])],
                        180, 70)
                else:
                    boats = ('Aucun', 180, 70)

                permit = PermitView(
                    applicant, boat=boats, site='Parc National de Port-Cros',
                    template=permit_model, save_path=f)
                permit.save()
                _elapsed = datetime.datetime.utcnow() - now
                current_app.logger.debug(
                    'Permit gen: {} ms'.format(_elapsed.total_seconds() * 1000))
    except Exception as e:
        traceback.print_exc()

    try:
        with current_app.open_resource(f, 'rb') as pdf:
            response = Response(pdf.read())
            response.mimetype = 'application/pdf'
            response.headers['Content-Disposition'] = (
                'attachment; filename={}'.format(os.path.basename(f)))
            return response
    except Exception as e:
        traceback.print_exc()
        err_type, err_value, tb = sys.exc_info()
        current_app.logger.warn(
            ''.join(format_exception_only(err_type, err_value)))
        return '500 error', 500

@permits.route('/api/permits', methods=['POST'])
@authenticateAdmin
def save_permit(reqUser):
    payload = request.get_json()
    dive_sites = payload['divesites']
    del payload['divesites']
    type_permit = TypePermit(**payload)

    try:
        db.session.query(TypePermit).filter(TypePermit.status == 'enabled').update({'status': 'disabled'})
        type_permit.template = str(payload['template'])
        db.session.add(type_permit)
        db.session.commit()

        type_permit_hearts = extract_permit_dive_sites(type_permit, dive_sites)
        db.session.add_all(type_permit_hearts)
        db.session.commit()

        users = User.query.all()
        emailBody = EmailTemplate(
            template=current_app.config['NEW_TYPE_PERMIT_TEMPLATE'],
            values={
                'title': current_app.config['NEW_TYPE_PERMIT_SUBJECT'],
                'serverUrl': current_app.config['SERVER_URL']
            }).render()

        for user in users:
            sendmail('no-reply@natural-solutions.eu', user.email,
                     current_app.config['NEW_TYPE_PERMIT_SUBJECT'], emailBody)
        return jsonify('success'), 200

    except (Exception) as e:
        traceback.print_exc()
        return jsonify('500 error'), 500

@permits.route('/api/typepermits', methods=['GET'])
@authenticateAdmin
def get_all_type_permits(reqUser):
    return jsonify([type_permit.json() for type_permit in TypePermit.query.\
                                order_by(desc(TypePermit.id)).\
                                all()])
@permits.route('/api/permits', methods=['GET'])
@authenticateAdmin
def get_all_permits(reqUser):
    return jsonify([permit.json() for permit in Permit.query.\
                                order_by(desc(Permit.id)).\
                                all()])

@permits.route('/api/me/permits', methods=['GET'])
@authenticate
def get_my_permits(reqUser):
    permit = Permit.query.\
                   filter(Permit.user_id == reqUser.id).\
                   order_by(desc(Permit.id)).\
                   first();
    if permit:
        return jsonify(permit.json())
    else:
        return jsonify(None)

@permits.route('/api/typepermits', methods=['PATCH'])
@authenticateAdmin
def update_type_permit(reqUser):
    try:
        typePermits = request.get_json()
        for typePermit in typePermits:
            permitPatch = {}
            for key, value in typePermit.items():
                if value != '':
                    permitPatch[key] = value
            db.session.query(TypePermit).filter(TypePermit.id == int(permitPatch['id'])).update(permitPatch)
            db.session.query(TypePermit).filter(TypePermit.id != int(permitPatch['id'])).update({'status': 'disabled'})
            db.session.commit()
        return jsonify('success'), 200
    except (Exception) as e:
        traceback.print_exc()
        return jsonify('500 error'), 500


def extract_permit_dive_sites( type_permit: TypePermit, dive_sites)-> Sequence[TypePermitHearts]:
    return [
        TypePermitHearts(
            type_permit_id=int(type_permit.id),
            dive_site_id=int(dive_site['id']))
        for dive_site in dive_sites
        ]