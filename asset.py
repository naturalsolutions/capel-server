from flask import (Blueprint, send_from_directory, jsonify)

assets = Blueprint('assets', __name__, static_folder='assets')


@assets.route('/assets/<path:path>')
def serve_assets(path):
    try:
        return send_from_directory('assets', path)
    except Exception:
        return jsonify('Resource not found'), 404
