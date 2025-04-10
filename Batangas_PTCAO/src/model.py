from datetime import datetime
from sqlalchemy import CheckConstraint, Enum as SqlEnum
from Batangas_PTCAO.src.extension import db
import bcrypt
from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    RESIGNED = 'resigned'


class PropertyStatus(str, Enum):
    ACTIVE = 'Active'
    MAINTENANCE = 'Maintenance'


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(50), nullable=False, unique=True)
    designation = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    gender = db.Column(db.String(10), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Property(db.Model):
    __tablename__ = 'property'

    property_id = db.Column(db.Integer, primary_key=True)
    property_name = db.Column(db.String(100), nullable=False)
    barangay = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    accommodation_type = db.Column(db.String(50))
    status = db.Column(SqlEnum(PropertyStatus, name="status_enum"), nullable=False, default=PropertyStatus.ACTIVE)
    description = db.Column(db.Text)

    rooms = db.relationship('Room', back_populates='property', cascade="all, delete-orphan")
    amenities = db.relationship('Amenity', back_populates='property', cascade="all, delete-orphan")
    typical_locations = db.relationship('TypicalLocation', back_populates='property', cascade="all, delete-orphan")
    coordinates = db.relationship('LongLat', back_populates='property', cascade="all, delete-orphan")


class Room(db.Model):
    __tablename__ = 'room'

    room_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    room_type = db.Column(db.String(50))
    day_price = db.Column(db.Numeric(10, 2))
    overnight_price = db.Column(db.Numeric(10, 2))
    capacity = db.Column(db.Integer)

    property = db.relationship('Property', back_populates='rooms')
    amenities = db.relationship('Amenity', back_populates='room', cascade="all, delete-orphan")


class Amenity(db.Model):
    __tablename__ = 'amenities'

    amenity_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=True)
    amenity = db.Column(db.String(255), nullable=False)

    property = db.relationship('Property', back_populates='amenities')
    room = db.relationship('Room', back_populates='amenities')


class TypicalLocation(db.Model):
    __tablename__ = 'typical_location'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    property = db.relationship('Property', back_populates='typical_locations')


class LongLat(db.Model):
    __tablename__ = 'longlat'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    longitude = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Integer, nullable=False)

    property = db.relationship('Property', back_populates='coordinates')
