import os
import sys
import datetime
from traceback import format_exception_only
from flask import (Blueprint, Response, current_app)

from auth import authenticate
from model import User

DATA_DIR = None

permits = Blueprint('permit', __name__)


def init_app(app):
    global DATA_DIR
    DATA_DIR = app.config['PERMITS_DIR']
    os.makedirs(DATA_DIR, exist_ok=True)


@permits.route('/api/users/<int:id>/permit.pdf', methods=['GET'])
def get_permit(id):
    response = None
    user = User.query.filter_by(id=id).first_or_404()
    if user is not None:
        now = datetime.datetime.utcnow()
        f = '/'.join([
            DATA_DIR,
            '_'.join(['Autorisation', 'PNPC',
                      str(now.year), str(user.firstname), str(user.id)])
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
                template=current_app.config['PERMIT_TEMPLATE'], save_path=f)
            permit.save()
            _elapsed = datetime.datetime.utcnow() - now
            current_app.logger.debug(
                'Permit gen: {} ms'.format(_elapsed.total_seconds() * 1000))

        try:
            with current_app.open_resource(f, 'rb') as pdf:
                response = Response(pdf.read())
                response.mimetype = 'application/pdf'
                response.headers['Content-Disposition'] = (
                    'attachment; filename={}'.format(os.path.basename(f)))
                return response
        except Exception as e:
            err_type, err_value, tb = sys.exc_info()
            current_app.logger.warn(
                ''.join(format_exception_only(err_type, err_value)))
            return '500 error', 500
