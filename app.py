from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask import request
from flask import make_response
from flask_cors import CORS
from functools import wraps
import jwt
import json

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/portcros.db'
db = SQLAlchemy(app)

jwtSecret = 'abcdef'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username
    
    def toJSON(self):
        return {\
            'id': self.id,\
            'username': self.username,\
            'password': self.password,\
            'email': self.email
        }

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token is None:
            return make_response('', 401)
        token = token.split(' ')[1]
        payload = jwt.decode(token, jwtSecret, algorithm='HS256')
        user = User.query.filter_by(id=payload['id']).first()
        if user is None:
            return make_response('', 403)
        
        return f(*args, user)
    return decorated_function

def authenticateOrNot(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token is None:
            return f(*args, None)
        token = token.split(' ')[1]
        payload = jwt.decode(token, jwtSecret, algorithm='HS256')
        user = User.query.filter_by(id=payload['id']).first()
        if user is None:
            return make_response('', 403)
        
        return f(*args, user)
    return decorated_function

@app.route("/")
def hello():
    return 'hello portcros-server !'

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        user = User.query.filter_by(username=request.json['username'], password=request.json['password']).first()
    except Exception as e:
        return jsonify(), 400
    
    if user is None:
        return jsonify(), 404

    payload = user.toJSON()
    token = jwt.encode(payload, jwtSecret, algorithm='HS256')

    return jsonify(token=token.decode('utf8'), profile=payload)

@app.route('/api/users/me')
@authenticate
def getMe(reqUser):
    reqUser = reqUser.toJSON()
    return jsonify(reqUser)

@app.route('/api/users', methods=['POST'])
@authenticateOrNot
def postUsers(reqUser):
    user = request.json
    user = User(**user)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.toJSON())

@app.route('/api/users', methods=['GET'])
@authenticateOrNot
def getUsers(reqUser):
    users = User.query.all()
    results = []
    for user in users:
        results.append(user.toJSON())

    return jsonify(results)