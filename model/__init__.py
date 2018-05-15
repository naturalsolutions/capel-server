import re
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from geoalchemy2 import Geometry
import json
import datetime

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


# Define the User data model. Make sure to add the flask_user.UserMixin !!
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
    boats = db.relationship('Boat', backref='users', lazy='dynamic')
    dives = db.relationship('Dive', backref='users', lazy='dynamic')
    createdAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username

    def toJSON(self):
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
            'createdAt': self.createdAt,
            'updatedAt': self.updatedAt
        }


class Boat(db.Model):

    __tablename__ = 'boats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))

    def __repr__(self):
        return '<Boat %r>' % self.name

    def toJSON(self):
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
    validity = db.Column(db.Unicode(255))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    endAt = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))  # noqa
    divesite_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))  # noqa


# Define the TypeDive data model
class TypeDive(db.Model):

    __tablename__ = 'typedives'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode(255))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<TypeDive %r>' % self.name

    def toJSON(self):
        return {
            'id': self.id,
            'name': self.name
        }


# Define the DiveSite data model
class DiveSite(db.Model):

    __tablename__ = 'divesites'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    referenced = db.Column(db.String)
    # Relationships
    geom = db.Column(Geometry('POLYGON'))


# Define the Dive data model
class Dive(db.Model):

    __tablename__ = 'dives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    divingDate = db.Column(db.DateTime)
    times = db.Column(db.ARRAY(db.Time, dimensions=2))
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))  # noqa
    divesite_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))  # noqa
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    weather_id = db.Column(db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))  # noqa
    weather = db.relationship("Weather", uselist=False, backref="dives", foreign_keys=[weather_id])  # noqa
    boats = db.relationship('Boat', secondary='diveboats', backref="dive")
    typeDives = db.relationship("TypeDive", secondary="divetypedives",  backref="dive")  # noqa
    # shop_id = db.Column(db.Integer(), db.ForeignKey('users.id')  # noqa
    # shop = db.relationship("User", foreign_keys=[shop_id])
    user = db.relationship("User", back_populates="dives")

    def toJSON(self):

        return {
            'id': self.id,
            'divingDate': self.divingDate,
            'weather': self.weather.toJSON(),
            'boats': [[boat.toJSON()] for boat in self.boats],
            'times': [[json.dumps(time, indent=4, sort_keys=True, default=str)] for time in self.times],  # noqa
            'typeDives': [[typeDive.toJSON()] for typeDive in self.typeDives],
            'user': self.user.toJSON()
        }


# Define the Weather data model
class Weather(db.Model):

    __tablename__ = 'weathers'
    __table_args__ = {'extend_existing': True}

    def __init__(self, sky, seaState, wind,
                 water_temperature, wind_temperature, visibility):
        self.sky = sky
        self.seaState = seaState
        self.wind = wind
        self.water_temperature = water_temperature
        self.wind_temperature = wind_temperature
        self.visibility = visibility

    id = db.Column(db.Integer(), primary_key=True)
    sky = db.Column(db.String(255))
    seaState = db.Column(db.String(255))
    wind = db.Column(db.String(255))
    water_temperature = db.Column(db.Integer())
    wind_temperature = db.Column(db.Integer())
    visibility = db.Column(db.Integer())
    #dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id'))
    dive = db.relationship("Dive", uselist=False, back_populates="weather")  # noqa

    def toJSON(self):
        return {
            'id': self.id,
            'sky': self.sky,
            'seaState': self.seaState,
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
    nbrDivers = db.Column(db.Integer())

    dive = db.relationship("Dive")
    typeDive = db.relationship("TypeDive")


# Define the DiveBoat data model
class DiveBoat(db.Model):

    __tablename__ = 'diveboats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))  # noqa
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id', ondelete='CASCADE'))  # noqa

    dive = db.relationship("Dive")
    boat = db.relationship("Boat")
