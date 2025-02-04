from extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    MAINTENANCE = 'maintenance'

class RegistrationStep(str, Enum):
    BUSINESS_DETAILS = 'business_details'
    SPECIAL_SERVICES = 'special_services'
    LOGIN_CREDENTIALS = 'login_credentials'

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    account_status = db.Column(db.String(20), default=AccountStatus.ACTIVE)
    failed_login_attempts = db.Column(db.Integer, default=0)
    business_registration = db.relationship('BusinessRegistration', backref='user', lazy=True)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_suspended(self):
        return self.account_status == AccountStatus.SUSPENDED

    def is_active(self):
        return self.account_status == AccountStatus.ACTIVE


class BusinessRegistration(db.Model):
    __tablename__ = 'businessregistration'

    business_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    business_registration_no = db.Column(db.String(100), nullable=False)
    business_name = db.Column(db.String(255), nullable=False)
    official_contact_no = db.Column(db.String(50), nullable=False)
    business_address = db.Column(db.String(255), nullable=False)
    taxpayer_name = db.Column(db.String(255), nullable=False)
    total_employees = db.Column(db.Integer, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    total_beds = db.Column(db.Integer, nullable=False)
    special_services = db.relationship('SpecialServices', backref='business', lazy=True)


class SpecialServices(db.Model):
    __tablename__ = 'special_services'

    service_id = db.Column(db.Integer, primary_key = True)
    business_id = db.Column(db.Integer, db.ForeignKey('businessregistration.business_id'), nullable=False)
    accreditation_type = db.Column(db.String(100), nullable=False)
    ae_classification = db.Column(db.String(100), nullable=False)
    amenities = db.Column(db.String(255), nullable=False)

class Room(db.Model):
    __tablename__ = 'rooms'

    room_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businessregistration.business_id'), nullable=False)
    room_type = db.Column(db.String(100), nullable=False)
    total_number = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Double, nullable=False, default=0.00)

class EventFacility(db.Model):
    __tablename__ = 'event_facilities'

    facility_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businessregistration.business_id'), nullable=False)
    room_name = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    facilities = db.Column(db.String(255), nullable=False)

class Amenity(db.Model):
    __tablename__ = 'amenities'

    amenity_id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businessregistration.business_id'), nullable=False)
    amenity = db.Column(db.String(255), nullable=False)


