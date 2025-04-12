from datetime import datetime
from sqlalchemy import CheckConstraint, Enum as SqlEnum
from Batangas_PTCAO.src.extension import db
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