import os
import sys
import datetime
from typing import Sequence
from traceback import format_exception_only
from flask import (Blueprint, Response, current_app, request, jsonify)
from model import User, TypePermit, db, TypePermitHearts, Permit
from auth import (authenticate, authenticateAdmin)
import base64
from pathlib import Path
from sqlalchemy import func
from sqlalchemy import desc
from mail import EmailTemplate, sendmail

DATA_DIR = None
tmpl_coords = {
    'date_and_permitid': (180, 151),
    'fullname': (156, 122),
    'phone': (135, 105),
    'email': (100, 88),
    'boats': (180, 70)
}
# TODO: font + font-size
permits = Blueprint('permits', __name__)


def init_app(app):
    global DATA_DIR
    DATA_DIR = app.config['PERMITS_DIR']
    os.makedirs(DATA_DIR, exist_ok=True)


@permits.route('/api/permits/count', methods=['GET'])
@authenticateAdmin
def get_count_users(reqUser):
    data = db.session.query(func.count(Permit.id)).scalar()
    return jsonify(data)


@permits.route('/api/users/<int:id>/permit.pdf', methods=['GET'])
def get_permit(id):  # noqa: A002
    try:
        f = None
        response = None
        user = User.query.filter_by(id=id).first_or_404()

        typePermit = TypePermit.query.filter_by(status='enabled').first()

        permit_model = os.path.join(
            current_app.config['PERMIT_PATH'],
            '.'.join([str(typePermit.id), 'pdf']))

        my_file = Path(permit_model)
        # current_app.logger.debug('permit_model:', permit_model)
        if not my_file.is_file():
            with open(permit_model, 'wb') as fout:
                fout.write(
                    base64.decodestring(bytes(typePermit.template, 'utf-8')))
        instance = db.session.query(Permit).filter_by(
            user_id=id, typepermit_id=typePermit.id).first()
        if instance is None:
            _permit = Permit()
            _permit.user_id = id
            _permit.typepermit_id = typePermit.id
            db.session.add(_permit)
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
            f = os.path.join(
                DATA_DIR,
                '_'.join([
                    'Autorisation', 'PNPC',
                    str(now.year), str(user.id), str(typePermit.id)]) + '.pdf')
            if not os.path.isfile(f):
                from .pdfmix import Applicant, PermitView

                applicant = Applicant([
                    ('.'.join([
                        str(instance.updated_at.strftime('%d-%m-%Y')),
                        str(instance.id)]),
                     *tmpl_coords['date_and_permitid']),
                    (' '.join([user.firstname, user.lastname]),
                     *tmpl_coords['fullname']),
                    (user.phone, *tmpl_coords['phone']),
                    (user.email, *tmpl_coords['email'])])

                boats = user.boats.all()
                if boats not in (None, []):
                    boats = ([', '.join([
                        ' '.join([boat.name, boat.matriculation])
                        for boat in user.boats])],
                        *tmpl_coords['boats'])
                else:
                    boats = ('Aucun', *tmpl_coords['boats'])

                permit = PermitView(
                    applicant, boat=boats, site='Parc National de Port-Cros',
                    template=permit_model, save_path=f)

                # current_app.logger.debug('permit filename:', f)

                permit.save()
                _elapsed = datetime.datetime.utcnow() - now
                current_app.logger.debug(
                    'Permit gen: {} ms'.format(_elapsed.total_seconds() * 1000))  # noqa: E501
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        current_app.logger.warn(exc_type, fname, exc_tb.tb_lineno)

    try:
        with current_app.open_resource(f, 'rb') as pdf:
            response = Response(pdf.read())
            response.mimetype = 'application/pdf'
            response.headers['Content-Disposition'] = (
                'attachment; filename={}'.format(os.path.basename(f)))
            return response
    except Exception:
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
        db.session.query(TypePermit).filter(TypePermit.status == 'enabled')\
                                    .update({'status': 'disabled'})
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
        current_app.logger.warn(e)
        return jsonify('500 error'), 500


@permits.route('/api/typepermits', methods=['GET'])
@authenticateAdmin
def get_all_type_permits(reqUser):
    return jsonify([
        type_permit.json()
        for type_permit in TypePermit.query
                                     .order_by(desc(TypePermit.id))
                                     .all()])


@permits.route('/api/permits', methods=['GET'])
@authenticateAdmin
def get_all_permits(reqUser):
    return jsonify([
        permit.json()
        for permit in Permit.query
                            .order_by(desc(Permit.id))
                            .all()])


@permits.route('/api/me/permits', methods=['GET'])
@authenticate
def get_my_permits(reqUser):
    permit = Permit.query\
                .filter(Permit.user_id == reqUser.id)\
                .order_by(desc(Permit.id))\
                .first()
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
            db.session.query(TypePermit)\
                      .filter(TypePermit.id == int(permitPatch['id']))\
                      .update(permitPatch)
            db.session.query(TypePermit)\
                      .filter(TypePermit.id != int(permitPatch['id']))\
                      .update({'status': 'disabled'})
            db.session.commit()
        return jsonify('success'), 200
    except Exception as e:
        current_app.logger.warn(e)
        return jsonify('500 error'), 500


def extract_permit_dive_sites(
        type_permit: TypePermit,
        dive_sites) -> Sequence[TypePermitHearts]:
    return [
        TypePermitHearts(
            type_permit_id=int(type_permit.id),
            dive_site_id=int(dive_site['id']))
        for dive_site in dive_sites
        ]
