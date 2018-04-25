from app import db
from geoalchemy2 import Geometry


# Define the Boat data model
class Boat(db.Model):

    __tablename__ = 'boats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)  # for display purposes
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))

    def __repr__(self):
        return '<Boat %r>' % self.name

    def toJSON(self):
        return {
            'id': self.id,
            'name': self.name,
            'matriculation': self.matriculation
        }

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



# Define the Permit data model
class Permit(db.Model):

    __tablename__ = 'permits'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # for @roles_accepted()
    url = db.Column(db.Unicode(255))  # for display purposes
    validity = db.Column(db.Unicode(255))  # for display purposes
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
    name = db.Column(db.Unicode(255))  # for display purposes

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
    referenced = db.Column(db.String)  # for display purposes
    # Relationships
    geom = db.Column(Geometry('POLYGON'))

# Define the Weather data model
class Weather(db.Model):

    __tablename__ = 'weathers'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    sky = db.Column(db.String(255))
    seaState = db.Column(db.String(255))
    wind = db.Column(db.String(255))
    water_temperature = db.Column(db.Integer())
    wind_temperature = db.Column(db.Integer())
    visibility = db.Column(db.Integer())

# Define the Dive data model
class Dive(db.Model):

    __tablename__ = 'dives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    divingDate = db.Column(db.DateTime)
    startTime = db.Column(db.DateTime)
    endTime = db.Column(db.DateTime)  # for display purposes
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    divesite_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))
    weather_id = db.Column(db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))

# Define the DiveTypeDive data model
class DiveTypeDive(db.Model):

    __tablename__ = 'divetypedives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    divetype_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    nbrDivers = db.Column(db.Integer())


# Define the DiveBoat data model
class DiveBoat(db.Model):

    __tablename__ = 'diveboats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id', ondelete='CASCADE'))



if __name__ == "__main__":
 # Run this file directly to create the database tables.
 print ("Creating database tables...")
 db.create_all()
 print("Done!'")
 print("Inserting Type Dive Data..!'")
 #db.session.add_all([ TypeDive("Baptême"), TypeDive("Exploration"),  TypeDive("Technique"), TypeDive("Randinnée palmeée"), TypeDive("Apneée") ])
 db.session.commit()
 print ("Done!'")
