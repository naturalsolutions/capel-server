from app import app
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry


# db.init(app)
db = SQLAlchemy(app)

__all__ = ['db', 'User', 'Boat', 'Permit',
           'TypeDive', 'DiveSite', 'Dive', 'DiveTypeDive', 'DiveBoat',
           'Weather']

# Define the User data model. Make sure to add the flask_user.UserMixin !!
class User(db.Model):

    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255))
    createdAt = db.Column(db.DateTime)

    boats = db.relationship('Boat', backref='users', lazy='dynamic')
    dives = db.relationship('Dive', backref='users', lazy='dynamic')


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
            'createdAt': self.createdAt.utcnow()
        }



# Define the Boat data model
class Boat(db.Model):

    __tablename__ = 'boats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Boat %r>' % self.name

    def toJSON(self):
        return {
            'id': self.id,
            'name': self.name,
            'matriculation': self.matriculation
        }



# Define the Permit data model
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
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    divesite_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))


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
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    divesite_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))
    weather_id = db.Column(db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    weather = db.relationship("Weather", uselist=False, backref="dives", foreign_keys=[weather_id])
    boats = db.relationship('Boat', secondary='diveboats', backref="dive")
    typeDives = db.relationship("TypeDive", secondary="divetypedives",  backref="dive")
    user = db.relationship("User", back_populates="dives")

# Define the Weather data model
class Weather(db.Model):

    __tablename__ = 'weathers'
    __table_args__ = {'extend_existing': True}

    def __init__(self, skey, seaState, wind, water_temperature, wind_temperature, visibility):
        self.skey = skey
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
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id'))
    dive = db.relationship("Dive", uselist=False, backref="weathers", foreign_keys=[dive_id])





# Define the DiveTypeDive data model
class DiveTypeDive(db.Model):

    __tablename__ = 'divetypedives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    divetype_id = db.Column(db.Integer(), db.ForeignKey('typedives.id', ondelete='CASCADE'))
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    nbrDivers = db.Column(db.Integer())

    dive = db.relationship("Dive")
    typeDive = db.relationship("TypeDive")


# Define the DiveBoat data model
class DiveBoat(db.Model):

    __tablename__ = 'diveboats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id', ondelete='CASCADE'))

    dive = db.relationship("Dive")
    boat = db.relationship("Boat")

#db.create_all()