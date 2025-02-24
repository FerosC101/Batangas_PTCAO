from sqlalchemy import CheckConstraint, ForeignKey, Enum
from Batangas_PTCAO.src.extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum as PyEnum
import bcrypt

# Enum Definitions
class AccountStatus(str, PyEnum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    MAINTENANCE = 'maintenance'

class RegistrationStep(str, PyEnum):
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

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> tuple[bool, bytes]:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def is_suspended(self):
        return self.account_status == AccountStatus.SUSPENDED

    def is_active(self):
        return self.account_status == AccountStatus.ACTIVE

class Establishment(db.Model):
    __tablename__ = 'establishments'

    establishment_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    establishment_type = db.Column(db.String(50))
    other_type_details = db.Column(db.String(100))
    date_established = db.Column(db.Date, nullable=False)
    tin = db.Column(db.String(20), unique=True, nullable=False)

    contact_details = db.relationship('ContactDetails', backref='establishment', lazy=True)
    dot_accreditation = db.relationship('DotAccreditation', backref='establishment', lazy=True)
    management_details = db.relationship('ManagementDetails', backref='establishment', lazy=True)
    employee_count = db.relationship('EmployeeCount', backref='establishment', lazy=True)
    rooms = db.relationship('Room', backref='establishment', lazy=True)
    function_rooms = db.relationship('FunctionRoom', backref='establishment', lazy=True)

class ContactDetails(db.Model):
    __tablename__ = 'contact_details'

    contact_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    landline = db.Column(db.String(20))
    mobile_number = db.Column(db.String(20))
    email_address = db.Column(db.String(255))
    website = db.Column(db.String(255))
    social_media_accounts = db.Column(db.Text)

class DotAccreditation(db.Model):
    __tablename__ = 'dot_accreditation'

    accreditation_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    is_accredited = db.Column(db.Boolean, nullable=False)
    category = db.Column(db.String(50))
    star_rating = db.Column(db.Integer)
    accreditation_type = db.Column(db.String(50))

class ManagementDetails(db.Model):
    __tablename__ = 'management_details'

    management_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    has_managing_company = db.Column(db.Boolean, nullable=False)
    managing_company_name = db.Column(db.String(255))
    managing_company_address = db.Column(db.Text)
    owner_manager_name = db.Column(db.String(255), nullable=False)
    organization_type = db.Column(db.String(50))

class EmployeeCount(db.Model):
    __tablename__ = 'employee_count'

    count_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    male_count = db.Column(db.Integer, nullable=False, default=0)
    female_count = db.Column(db.Integer, nullable=False, default=0)

class AccreditationType(db.Model):
    __tablename__ = 'accreditation_types'

    accreditation_type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), unique=True, nullable=False)

class AEClassification(db.Model):
    __tablename__ = 'ae_classifications'

    classification_id = db.Column(db.Integer, primary_key=True)
    classification_name = db.Column(db.String(100), unique=True, nullable=False)

class RoomType(db.Model):
    __tablename__ = 'room_types'

    room_type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), unique=True, nullable=False)

class Room(db.Model):
    __tablename__ = 'rooms'

    room_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    room_type_id = db.Column(db.Integer, ForeignKey('room_types.room_type_id'), nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    amenities = db.relationship('RoomAmenity', backref='room', lazy=True)

class FunctionRoom(db.Model):
    __tablename__ = 'function_rooms'

    function_room_id = db.Column(db.Integer, primary_key=True)
    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), nullable=False)
    room_name = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    facilities = db.relationship('FunctionRoomFacility', backref='function_room', lazy=True)

class Facility(db.Model):
    __tablename__ = 'facilities'

    facility_id = db.Column(db.Integer, primary_key=True)
    facility_name = db.Column(db.String(100), unique=True, nullable=False)

class FunctionRoomFacility(db.Model):
    __tablename__ = 'function_room_facilities'

    function_room_id = db.Column(db.Integer, ForeignKey('function_rooms.function_room_id'), primary_key=True)
    facility_id = db.Column(db.Integer, ForeignKey('facilities.facility_id'), primary_key=True)

class Amenity(db.Model):
    __tablename__ = 'amenities'

    amenity_id = db.Column(db.Integer, primary_key=True)
    amenity_name = db.Column(db.String(100), unique=True, nullable=False)

class RoomAmenity(db.Model):
    __tablename__ = 'room_amenities'

    room_id = db.Column(db.Integer, ForeignKey('rooms.room_id'), primary_key=True)
    amenity_id = db.Column(db.Integer, ForeignKey('amenities.amenity_id'), primary_key=True)

class EstablishmentAccreditation(db.Model):
    __tablename__ = 'establishment_accreditation'

    establishment_id = db.Column(db.Integer, ForeignKey('establishments.establishment_id'), primary_key=True)
    accreditation_type_id = db.Column(db.Integer, ForeignKey('accreditation_types.accreditation_type_id'), primary_key=True)
    ae_classification_id = db.Column(db.Integer, ForeignKey('ae_classifications.classification_id'), primary_key=True)