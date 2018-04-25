from app import app
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Index
# from geoalchemy2 import Geometry
import geoalchemy2 as geo


# db.init(app)
db = SQLAlchemy(app)

__all__ = ['db', 'User', 'Boat', 'Permit',
           'TypeDive', 'DiveSite', 'Dive', 'DiveTypeDive', 'DiveBoat',
           'Weather']


# Define the User data model. Make sure to add the flask_user.UserMixin !!
class User(db.Model):
    __tablename__ = 'users'
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

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # do custom initialization here

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
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)
    user_id = db.Column(
        db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))


# Define the Permit data model
class Permit(db.Model):
    __tablename__ = 'permits'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    url = db.Column(db.Unicode(255))
    validity = db.Column(db.Unicode(255))
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    endAt = db.Column(db.DateTime)
    user_id = db.Column(
        db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    divesite_id = db.Column(
        db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))


# Define the TypeDive data model
class TypeDive(db.Model):
    __tablename__ = 'typedives'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)


# Define the DiveSite data model
class DiveSite(db.Model):
    __tablename__ = 'divesites'
    id = db.Column(db.Integer(), primary_key=True)
    referenced = db.Column(db.String)
    # Relationships
    # geom = db.Column(geo.Geometry('POLYGON'))
    geom = db.Column(geo.Geometry(geometry_type='POLYGON', spatial_index=False))


# Index('idx_site_polygon', DiveSite.__table__.c.geom, postgres_using='gist')


# Define the Weather data model
class Weather(db.Model):
    __tablename__ = 'weathers'
    id = db.Column(db.Integer(), primary_key=True)
    sky_id = db.Column(db.Integer())
    seaState_id = db.Column(db.Integer())
    wind_id = db.Column(db.Integer())
    water_temperature = db.Column(db.Integer())
    wind_temperature = db.Column(db.Integer())
    visibility = db.Column(db.Integer())


# Define the Dive data model
class Dive(db.Model):
    __tablename__ = 'dives'
    id = db.Column(db.Integer(), primary_key=True)
    divingDate = db.Column(db.DateTime)
    startTime = db.Column(db.DateTime)
    endTime = db.Column(db.DateTime)
    user_id = db.Column(
        db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    divesite_id = db.Column(
        db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))
    weather_id = db.Column(
        db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))


# Define the DiveTypeDive data model
class DiveTypeDive(db.Model):
    __tablename__ = 'divetypedives'
    id = db.Column(db.Integer(), primary_key=True)
    divetype_id = db.Column(db.Integer(), db.ForeignKey('divesites.id',
                                                        ondelete='CASCADE'))
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id',
                                                    ondelete='CASCADE'))
    nbrDivers = db.Column(db.Integer())


# Define the DiveBoat data model
class DiveBoat(db.Model):
    __tablename__ = 'diveboats'
    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id',
                                                    ondelete='CASCADE'))
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id',
                                                    ondelete='CASCADE'))


if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print("Creating database tables...")
    db.create_all()
    print("Done!'")
