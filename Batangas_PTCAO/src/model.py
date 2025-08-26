from datetime import datetime
from sqlalchemy import CheckConstraint, Enum as SqlEnum
from extension import db
import bcrypt
from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    RESIGNED = 'resigned'


class PropertyStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    MAINTENANCE = 'MAINTENANCE'


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
    is_archived = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except ValueError as e:
            return False

    @property
    def status(self):
        if self.is_active:
            return "archived"
        return "active" if self.is_active else "suspended"

class Property(db.Model):
    __tablename__ = 'property'

    property_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    property_name = db.Column(db.String(100), nullable=False)
    barangay = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    accommodation_type = db.Column(db.String(50))
    status = db.Column(SqlEnum(PropertyStatus), nullable=False, default=PropertyStatus.ACTIVE)
    description = db.Column(db.Text)

    rooms = db.relationship('Room', back_populates='property', cascade="all, delete-orphan")
    amenities = db.relationship('Amenity', back_populates='property', cascade="all, delete-orphan")
    typical_locations = db.relationship('TypicalLocation', back_populates='property', cascade="all, delete-orphan")
    coordinates = db.relationship('LongLat', back_populates='property', cascade="all, delete-orphan")
    images = db.relationship('PropertyImage', back_populates='property', cascade="all, delete-orphan")

class PropertyImage(db.Model):
    __tablename__ = 'property_images'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

    property = db.relationship('Property', back_populates='images')

class Room(db.Model):
    __tablename__ = 'room'

    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    room_type = db.Column(db.String(50))
    day_price = db.Column(db.Numeric(10, 2))
    overnight_price = db.Column(db.Numeric(10, 2))
    capacity = db.Column(db.Integer)

    property = db.relationship('Property', back_populates='rooms')
    amenities = db.relationship('Amenity', back_populates='room', cascade="all, delete-orphan")


class Amenity(db.Model):
    __tablename__ = 'amenities'

    amenity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    property = db.relationship('Property', back_populates='coordinates')

from datetime import datetime
from sqlalchemy import CheckConstraint, Enum as SqlEnum
from extension import db
from enum import Enum


class VisitorType(str, Enum):
    LOCAL = 'Local'
    FOREIGN = 'Foreign'


class StayType(str, Enum):
    DAY_TOUR = 'Day Tour'
    OVERNIGHT = 'Overnight'


class Event(db.Model):
    __tablename__ = 'events'

    event_id = db.Column(db.Integer, primary_key=True)
    event_title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    municipality = db.Column(db.String(100))
    location = db.Column(db.String(255))
    event_image = db.Column(db.String(255))  # file path
    category = db.Column(db.String(100))

    def __repr__(self):
        return f'<Event {self.event_title}>'


class VisitorStatistics(db.Model):
    __tablename__ = 'visitor_statistics'

    stat_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    visitor_type = db.Column(SqlEnum(VisitorType, name="visitor_type_enum"), nullable=False)
    stay_type = db.Column(SqlEnum(StayType, name="stay_type_enum"), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = db.relationship('Property', backref=db.backref('visitor_stats', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('property_id', 'report_date', 'visitor_type', 'stay_type', name='unique_visitor_stat'),
    )

    def __repr__(self):
        return f'<VisitorStat {self.property_id}-{self.report_date}-{self.visitor_type}-{self.stay_type}>'


class BarangayMonthlyStatistics(db.Model):
    __tablename__ = 'barangay_monthly_statistics'

    stat_id = db.Column(db.Integer, primary_key=True)
    barangay = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    local_visitors = db.Column(db.Integer, nullable=False, default=0)
    foreign_visitors = db.Column(db.Integer, nullable=False, default=0)
    day_tour_visitors = db.Column(db.Integer, nullable=False, default=0)
    overnight_visitors = db.Column(db.Integer, nullable=False, default=0)
    total_visitors = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('barangay', 'year', 'month', name='unique_barangay_month_stat'),
        CheckConstraint('month >= 1 AND month <= 12', name='valid_month_check'),
    )

    def __repr__(self):
        return f'<BarangayStat {self.barangay}-{self.year}-{self.month}>'


class PropertyMonthlyStatistics(db.Model):
    __tablename__ = 'property_monthly_statistics'

    stat_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    local_visitors = db.Column(db.Integer, nullable=False, default=0)
    foreign_visitors = db.Column(db.Integer, nullable=False, default=0)
    day_tour_visitors = db.Column(db.Integer, nullable=False, default=0)
    overnight_visitors = db.Column(db.Integer, nullable=False, default=0)
    total_visitors = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = db.relationship('Property', backref=db.backref('monthly_stats', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('property_id', 'year', 'month', name='unique_property_month_stat'),
        CheckConstraint('month >= 1 AND month <= 12', name='valid_month_check'),
    )

    def __repr__(self):
        return f'<PropertyStat {self.property_id}-{self.year}-{self.month}>'

# Add to model.py
class VisitorRecord(db.Model):
    __tablename__ = 'visitor_records'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(20), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    visitor_type = db.Column(SqlEnum(VisitorType, name="visitor_type_enum"), nullable=False)
    stay_type = db.Column(SqlEnum(StayType, name="stay_type_enum"), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    barangay = db.Column(db.String(100), nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=0)
    children = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = db.relationship('Property', backref=db.backref('visitor_records', lazy='dynamic'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.record_id = f"VR-{datetime.now().strftime('%Y%m%d')}-{self.id or 0:04d}"

    def __repr__(self):
        return f'<VisitorRecord {self.record_id}>'

class VisitorDataUpload(db.Model):
    __tablename__ = 'user_data_uploads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    records_processed = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship('User', backref=db.backref('data_uploads', lazy='dynamic'))

class PropertyReport(db.Model):
    __tablename__ = 'property_reports'

    report_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    dot_accredited = db.Column(db.Boolean, default=False)
    dot_accreditation_valid = db.Column(db.Date)
    ptcao_registered = db.Column(db.Boolean, default=False)
    ptcao_valid_until = db.Column(db.Date)
    classification = db.Column(db.String(50))
    male_employees = db.Column(db.Integer, default=0)
    female_employees = db.Column(db.Integer, default=0)
    total_rooms = db.Column(db.Integer, default=0)
    daytour_capacity = db.Column(db.Integer, default=0)
    overnight_capacity = db.Column(db.Integer, default=0)
    report_period_start = db.Column(db.Date, nullable=False)
    report_period_end = db.Column(db.Date, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship('Property', backref=db.backref('property_reports', lazy='dynamic'))

class TouristReport(db.Model):
    __tablename__ = 'tourist_reports'

    report_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    total_daytour_guests = db.Column(db.Integer, default=0)
    total_overnight_guests = db.Column(db.Integer, default=0)
    rooms_occupied = db.Column(db.Integer, default=0)
    foreign_daytour_visitors = db.Column(db.Integer, default=0)
    foreign_overnight_visitors = db.Column(db.Integer, default=0)
    male_tourists = db.Column(db.Integer, default=0)
    female_tourists = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Numeric(12, 2), default=0.00)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    property = db.relationship('Property', backref=db.backref('tourist_reports', lazy='dynamic'))

# Add to model.py (at the end)
class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    municipality = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class DestinationType(str, Enum):
    MOUNTAIN = 'Mountain'
    HERITAGE = 'Heritage'
    BEACH = 'Beach'
    ISLAND = 'Island'
    OTHER = 'Other'


class Destination(db.Model):
    __tablename__ = 'destinations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location_name = db.Column(db.String(100), nullable=False)  # Display name for location
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    barangay = db.Column(db.String(100), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    destination_type = db.Column(SqlEnum(DestinationType), nullable=False)
    image_path = db.Column(db.String(255))  # Optional image path
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Destination {self.name}>'