import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from geoalchemy2 import Geometry
from sqlalchemy import text

DUPLICATE_KEY_ERROR_REGEX = r'DETAIL:\s+Key \((?P<duplicate_key>.*)\)=\(.*\) already exists.'

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

def not_null_constraint_error(error):
    print('la')
    print(error)
    regexp_detail = r' (?P<value>.*) value in column "(?P<column>.*)" violates'
    match_detail = re.search(regexp_detail, error)
    column = match_detail.group('column')
    value = match_detail.group('value')
    regexp_table = r'INSERT INTO (?P<table>.*)'
    match_table = re.search(regexp_table, error)
    table = match_table.group('table').split(' ')[0]
    
    return {
        'table': table,
        'column': column,
        'value': value,
        'name': 'missing_attribute'
    }

def unique_constraint_error(error):
    regexp_detail = r'DETAIL:\s+Key \((?P<column>.*)\)=\((?P<value>.*)\) already exists.'
    match_detail = re.search(regexp_detail, error)
    column = match_detail.group('column')
    value = match_detail.group('value')
    regexp_table = r'violates unique constraint "(?P<table>.*)_' + re.escape(column) + r'_key"'
    match_table = re.search(regexp_table, error)
    table = match_table.group('table')
    return {
        'table': table,
        'column': column,
        'value': value,
        'name': 'value_exists'
    }

class User(db.Model):

    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    category = db.Column(db.String(64), nullable=True)
    address = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(255), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    zip = db.Column(db.String(255), nullable=True)
    common = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    firstname = db.Column(db.String(255), nullable=True)
    lastname = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = db.Column(db.String(255), nullable=True)
    photo = db.Column(db.Text())
    boats = db.relationship('Boat', backref='users', lazy='dynamic')
    offenses = db.relationship('Offense', backref='users', lazy='dynamic')
    diveSites = db.relationship('DiveSite', backref='users', lazy='dynamic')
    dives = db.relationship('Dive', backref='users', lazy='dynamic', foreign_keys='Dive.user_id')

    def __repr__(self):
        return '<User %r>' % self.username

    def json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'category': self.category,
            'address': self.address,
            'zip': self.zip,
            'website': self.website,
            'common': self.common,
            'city': self.city,
            'company': self.company,
            'country': self.country,
            'phone': self.phone,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'role': self.role,
            'status': self.status,
            'review': self.review,
            'photo': self.photo,
            'created_at': self.created_at,
            'boats': [boat.json() for boat in self.boats if boat.status != 'removed'],
            'offenses': [offense.json() for offense in self.offenses],
            'nbr_dives': len(self.dives)
        }


class Boat(db.Model):

    __tablename__ = 'boats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    matriculation = db.Column(db.Unicode(255), unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Unicode(255), default='enabled')

    def __repr__(self):
        return '<Boat %r>' % self.name

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'matriculation': self.matriculation,
            'status': self.status
        }

class Offense(db.Model):

    __tablename__ = 'offenses'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Unicode(255), default='enabled')

    def __repr__(self):
        return '<Offense %r>' % self.id

    def json(self):
        return {
            'id': self.id,
            'start_at': self.start_at,
            'end_at': self.end_at,
            'status': self.status
        }

class Permit(db.Model):

    __tablename__ = 'permits'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    status = db.Column(db.Unicode(255))
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship('User', foreign_keys='Permit.user_id')
    typepermit_id = db.Column(db.Integer(), db.ForeignKey('typepermits.id'), nullable=True)
    typepermit = db.relationship('TypePermit', foreign_keys='Permit.typepermit_id')
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    def json(self):
        return {
            'id': self.id,
            'status': self.status,
            'user': self.user.json(),
            'typepermit':self.typepermit.json(),
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }



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

class TypePermit(db.Model):

    __tablename__ = 'typepermits'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    template = db.Column(db.Text())
    status = db.Column(db.Unicode(255))
    caption = db.Column(db.Unicode(255))
    dive_sites = db.relationship('DiveSite', secondary='typepermithearts', backref='type_permit')

    def json(self):
        return {
            'id': self.id,
            'start_at': self.start_at,
            'end_at': self.end_at,
            'template': self.template,
            'status': self.status,
            'caption': self.caption,
            'dive_sites': [dive_site.cusJson() for dive_site in self.dive_sites]
        }

class TypePermitHearts(db.Model):
    __tablename__ = 'typepermithearts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    type_permit_id = db.Column(db.Integer(), db.ForeignKey('typepermits.id', ondelete='CASCADE'))
    dive_site_id = db.Column(db.Integer(), db.ForeignKey('divesites.id', ondelete='CASCADE'))
    dive_site = db.relationship("DiveSite", uselist=False, foreign_keys=[dive_site_id])
    type_permit = db.relationship('TypePermit', uselist=False, foreign_keys=[type_permit_id])

    def json(self):
        return {
            'id': self.id,
            'dive_site': self.dive_site.json(),
            'type_permit': self.type_permit.json()
        }


class DiveSite(db.Model):

    __tablename__ = 'divesites'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    referenced = db.Column(db.String)
    geom_mp = db.Column(Geometry('MULTIPOINT'))
    geom_poly = db.Column(Geometry('MultiPolygon'))
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    category = db.Column(db.String())
    status = db.Column(db.String())
    privacy = db.Column(db.String())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    heart_id = db.Column(db.Integer(), db.ForeignKey('divesites.id'), nullable=True)


    def all_sites():

        sql = text("select id, "
                   "name, "
                   "referenced, "
                   "latitude, "
                   "longitude, "
                   "heart_id, "
                   "user_id, "
                   "ST_AsGeoJSON(geom_poly) as geom_poly, "
                   "ST_AsGeoJSON(geom_mp) as geom_mp,"
                   "privacy,"
                   "category"
                   " from divesites "
                   "where category = 'site'")
        result = db.engine.execute(sql)
        diveSites = []
        for row in result:
            diveSites.append(DiveSite(**row)
                             )
        return diveSites

    def all_hearts():

        sql = text("select id, "
                   "name, "
                   "referenced, "
                   "latitude, "
                   "longitude, "
                   "heart_id, "
                   "user_id, "
                   "ST_AsGeoJSON(geom_poly) as geom_poly, "
                   "ST_AsGeoJSON(geom_mp) as geom_mp,"
                     "privacy"
                   " from divesites "
                   "where category = 'coeur' and status='enabled' ")
        result = db.engine.execute(sql)
        diveSites = []
        for row in result:
            diveSites.append(DiveSite(**row)
                             )
        return diveSites

    def getHeartsByPoint(latitude, longitude):

        sql = text("select id, "
                   "name, "
                   "referenced, "
                   "latitude, "
                   "longitude, "
                   "heart_id, "
                   "user_id, "
                   "ST_AsGeoJSON(geom_poly) as geom_poly, "
                   "ST_AsGeoJSON(geom_mp) as geom_mp,"
                   " privacy "
                   " from divesites "
                   "where category = 'coeur' and status='enabled' "
                   "and  st_contains(geom_poly, ST_GeomFromText('POINT("+longitude+ " "+latitude+")', 4326))")
        result = db.engine.execute(sql)
        diveSites = []
        for row in result:
            diveSites.append(DiveSite(**row)
                             )
        return diveSites

    def getOwnUserSite(user):

        sql = text("select distinct id, "
                   "name, "
                   "referenced, "
                   "latitude, "
                   "longitude, "
                   "heart_id, "
                   "user_id, "
                   "ST_AsGeoJSON(geom_poly) as geom_poly, "
                   "ST_AsGeoJSON(geom_mp) as geom_mp,"
                   " privacy "
                   " from divesites "
                   "where id in (select site_id from dives where user_id = '"+str(user.id)+"') "
                   )
        result = db.engine.execute(sql)
        diveSites = []
        for row in result:
            diveSites.append(DiveSite(**row)
                             )
        return diveSites

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'referenced': self.referenced,
            'geom_mp': self.geom_mp,
            'geom_poly': self.geom_poly,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'privacy': self.privacy,
            'user_id': self.user_id,
            'heart_id': self.heart_id

        }

    def cusJson(self):
        return {
            'id': self.id,
            'name': self.name,
            'referenced': self.referenced,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'privacy': self.privacy,
            'user_id': self.user_id,
            'heart_id': self.heart_id
        }



class Dive(db.Model):

    __tablename__ = 'dives'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime)
    times = db.Column(db.ARRAY(db.Time, dimensions=2))

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', back_populates='dives', foreign_keys='Dive.user_id')
    shop_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    shop = db.relationship("User", foreign_keys='Dive.shop_id')

    boats = db.relationship('Boat', secondary='diveboats', backref='dive')
    #dive_types = db.relationship('TypeDive', secondary='divetypedives',  backref='dive')

    site_id = db.Column(db.Integer(), db.ForeignKey('divesites.id'), nullable=True)
    dive_site = db.relationship("DiveSite", uselist=False, foreign_keys=[site_id])

    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    comment = db.Column(db.Text())
    weather_id = db.Column(db.Integer(), db.ForeignKey('weathers.id', ondelete='CASCADE'))
    weather = db.relationship("Weather", uselist=False, foreign_keys=[weather_id])

    divetypedives = db.relationship('DiveTypeDive', backref='users', lazy='dynamic', foreign_keys='DiveTypeDive.dive_id')


    def json(self):

        return {
            'id': self.id,
            'divingDate': self.date,
            'comment': self.comment,
            'weather': self.weather.json(),
            'boats': [boat.json() for boat in self.boats],
            'times': [[time[0].__str__(), time[1].__str__()] for time in self.times],
            'user': self.user.json(),
            'shop': self.shop.json() if self.shop else '',
            'dive_site': self.dive_site.cusJson(),
            'divetypedives': [divetypedive.json() for divetypedive in self.divetypedives]
        }


class Weather(db.Model):

    __tablename__ = 'weathers'
    __table_args__ = {'extend_existing': True}

    def __init__(self, sky, sea, wind,
                 water_temperature = 0, wind_temperature = 0, visibility = 0):
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
    divetype_id = db.Column(db.Integer(), db.ForeignKey('typedives.id', ondelete='CASCADE'))
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    divers = db.Column(db.Integer())
    dive = db.relationship('Dive')
    typeDive = db.relationship('TypeDive')

    def json(self):
        return {
            'id': self.id,
            'typeDive': self.typeDive.json(),
            'divers': self.divers
        }


class DiveBoat(db.Model):

    __tablename__ = 'diveboats'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    dive_id = db.Column(db.Integer(), db.ForeignKey('dives.id', ondelete='CASCADE'))
    boat_id = db.Column(db.Integer(), db.ForeignKey('boats.id', ondelete='CASCADE'))

    dive = db.relationship('Dive')
    boat = db.relationship('Boat')
