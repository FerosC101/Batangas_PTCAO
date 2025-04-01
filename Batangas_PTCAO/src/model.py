from datetime import datetime

from sqlalchemy import CheckConstraint

from Batangas_PTCAO.src.extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import bcrypt


class AccountStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    RESIGNED = 'resigned'


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
        return f'<MTOUser {self.username}>'

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password:str) -> tuple[bool, bytes]:
        return bcrypt.checkpw('utf-8'), self.password_hash.encode('utf-8')

    def is_suspended(self):
        return self.account_status == AccountStatus.SUSPENDED

    def is_active(self):
        return self.account_status == AccountStatus.ACTIVE

