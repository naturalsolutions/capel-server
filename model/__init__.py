import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from geoalchemy2 import Geometry
import json

DUPLICATE_KEY_ERROR_REGEX = r'DETAIL:\s+Key \((?P<duplicate_key>.*)\)=\(.*\) already exists.'  # noqa

db = SQLAlchemy()
migrate = Migrate()

__all__ = ['db', 'migrate', 'User', 'Boat', 'Permit',
           'TypeDive', 'DiveSite', 'Dive', 'DiveTypeDive', 'DiveBoat',
           'Weather', 'not_null_constraint_key', 'unique_constraint_key']


def not_null_constraint_key(error):
    return error.split('violates not-null constraint')[0] \
                .split('column')[1].strip().replace('"', '')


def unique_constraint_key(error):
    m = re.search(DUPLICATE_KEY_ERROR_REGEX, error)
    return m.group('duplicate_key')


class User(db.Model):

    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    category = db.Column(db.String(64), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    firstname = db.Column(db.String(255), nullable=True)
    lastname = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # noqa

    boats = db.relationship('Boat', backref='users', lazy='dynamic')
    dives = db.relationship('Dive', backref='users', lazy='dynamic', foreign_keys='Dive.user_id')  # noqa

    def __repr__(self):
        return '<User %r>' % self.username

    def json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'category': self.category,
            'address': self.address,
            'phone': self.phone,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'status': self.status,
            'createdAt': self.created_at
        }


class Boat(db.Model):

    __tablename__ = 'boats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Boat %r>' % self.name

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'matriculation': self.matriculation
        }


class Permit(db.Model):

    __tablename__ = 'permits'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    url = db.Column(db.Unicode(255))
    status = db.Column(db.Unicode(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))  # noqa
    site_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))  # noqa


class TypeDive(db.Model):
    # {"id": 1, "name": "Baptême"},
    # {"id": 2, "name": "Exploration"},
    # {"id": 4, "name": "Technique"},
    # {"id": 8, "name": "Randonnée palmée"},
    # {"id": 16, "name": "Apnée"}
    __tablename__ = 'typedives'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<TypeDive %r>' % self.name

    def json(self):
        return {
            'id': self.id,
            'name': self.name
        }


class DiveSite(db.Model):

    __tablename__ = 'divesites'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    referenced = db.Column(db.String)
    geom = db.Column(Geometry('POLYGON'))


class Dive(db.Model):

    __tablename__ = 'dives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime)
    times = db.Column(db.ARRAY(db.Time, dimensions=2))

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))  # noqa
    user = db.relationship('User', back_populates='dives', foreign_keys='Dive.user_id')  # noqa
    shop_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    shop = db.relationship("User", foreign_keys='Dive.shop_id')

    boats = db.relationship('Boat', secondary='diveboats', backref='dive')
    dive_types = db.relationship('TypeDive', secondary='divetypedives',  backref='dive')  # noqa

    site_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))  # noqa
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    weather_id = db.Column(db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))  # noqa
    weather = db.relationship("Weather", uselist=False, foreign_keys=[weather_id])  # noqa
    def json(self):

        return {
            'id': self.id,
            'divingDate': self.date,
            'weather': self.weather.json(),
            'boats': [[boat.json()] for boat in self.boats],
            'times': [[time[0].__str__(), time[1].__str__()] for time in self.times],  # noq
            'typeDives': [[d.json()] for d in self.dive_types],
            'user': self.user.json()
        }


class Weather(db.Model):

    __tablename__ = 'weathers'
    __table_args__ = {'extend_existing': True}

    def __init__(self, sky, sea, wind,
                 water_temperature, wind_temperature, visibility):
        self.sky = sky
        self.sea = sea
        self.wind = wind
        self.water_temperature = water_temperature
        self.wind_temperature = wind_temperature
        self.visibility = visibility

    id = db.Column(db.Integer(), primary_key=True)
    sky = db.Column(db.String(255))
    sea = db.Column(db.String(255))
    wind = db.Column(db.String(255))
    water_temperature = db.Column(db.Integer())
    wind_temperature = db.Column(db.Integer())
    visibility = db.Column(db.Integer())

    def json(self):
        return {
            'id': self.id,
            'sky': self.sky,
            'seaState': self.sea,
            'wind': self.wind,
            'water_temperature': self.water_temperature,
            'wind_temperature': self.wind_temperature,
            'visibility': self.visibility
        }


class DiveTypeDive(db.Model):

    __tablename__ = 'divetypedives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    divetype_id = db.Column(db.Integer(), db.ForeignKey('typedives.id', ondelete='CASCADE'))  # noqa
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))  # noqa
    divers = db.Column(db.Integer())
    dive = db.relationship('Dive')
    typeDive = db.relationship('TypeDive')


class DiveBoat(db.Model):

    __tablename__ = 'diveboats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))  # noqa
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id', ondelete='CASCADE'))  # noqa

    dive = db.relationship('Dive')
    boat = db.relationship('Boat')
