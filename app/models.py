from datetime import datetime
from hashlib import md5

from flask import url_for
from sqlalchemy import Boolean, CheckConstraint, Column, Date, Enum, ForeignKey, Integer, SmallInteger, String, \
    Sequence, Table, Text, UniqueConstraint, text, MetaData, DateTime
from sqlalchemy.orm import relationship, validates

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

metadata = MetaData()

account_types = Enum('Seeker', 'Company', 'Admin', name='account_types')
skill_types = Enum('tech', 'biz', name='skill_types')


class Attitude(db.Model):
    __tablename__ = 'attitude'

    id = Column(Integer, primary_key=True)
    title = Column(String(191), nullable=False, unique=True)

    def __repr__(self):
        return f"Attitude[{self.title}]"


class Skill(db.Model):
    __tablename__ = 'skill'

    id = Column(Integer, primary_key=True)
    title = Column(String(191), nullable=False, unique=True)
    type = Column(skill_types, nullable=False)

    def __repr__(self):
        return f"{self.type.capitalize()}Skill[{self.title}]"


class User(UserMixin, db.Model):
    __tablename__ = 'useraccount'

    id = Column(Integer, primary_key=True)
    account_type = Column(account_types, nullable=False)
    email = Column(String(191), nullable=False, unique=True)
    password = Column(String(191), nullable=False)

    is_active = Column(Boolean, default=True)
    join_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        status = ("" if self.is_active else "Non") + "Active"
        return f"{status}{self.account_type}User[{self.email}]"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def to_dict(self):
        data = {
            'id': self.id,
            'account_type': self.account_type,
            'email': self.email,
            'is_active': self.is_active,
            'join_date': self.join_date.isoformat() + 'Z',
            'last_login': self.last_login.isoformat() + 'Z',
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        return data

    def from_dict(self, data):
        for field, value in data.items():
            if field == 'password':
                self.set_password(value)
            else:
                setattr(self, field, value)


class CompanyProfile(db.Model):  # one to one with company-type user account
    __tablename__ = 'companyprofile'

    id = Column(Integer, primary_key=True)
    company_id = Column('company_id', ForeignKey('useraccount.id'), nullable=False, unique=True)
    name = Column(String(191), server_default=text("NULL"))
    city = Column(String(191), server_default=text("NULL"))
    state = Column(String(2), server_default=text("NULL"))
    website = Column(String(191), server_default=text("NULL"))

    job_posts = relationship("JobPost", back_populates="company")

    def __repr__(self):
        return f"CompanyProfile[{self.name}]"

    @validates('company_id')
    def validate_account(self, key, company_id):
        acct = User.query.filter_by(id=company_id).first()
        if acct is None:
            raise ValueError(f"No account w/id={company_id}")
        enum_company = account_types.enums[1]
        if enum_company != 'Company':
            raise ValueError(f"Sanity check failed. 'Company' not at enums[1].")
        if acct.account_type != enum_company:
            raise ValueError(f"Account type is not a Company")
        return company_id


class SeekerProfile(db.Model):  # one to one with seeker-type user account
    __tablename__ = 'seekerprofile'

    id = Column(Integer, primary_key=True)
    seeker_id = Column(ForeignKey('useraccount.id'), nullable=False, unique=True)
    first_name = Column(String(191), nullable=False)
    last_name = Column(String(191), nullable=False)
    phone_number = Column(Integer)
    city = Column(String(191), server_default=text("NULL"))
    state = Column(String(2), server_default=text("NULL"))

    @validates('seeker_id')
    def validate_account(self, key, seeker_id):
        acct = User.query.filter_by(id=seeker_id).first()
        if acct is None:
            raise ValueError(f"No account w/id={seeker_id}")
        enum_seeker = account_types.enums[0]
        if enum_seeker != 'Seeker':
            raise ValueError(f"Sanity check failed. 'Seeker' not at enums[0].")
        if acct.account_type != enum_seeker:
            raise ValueError(f"Account type is not a Seeker")
        return seeker_id


class JobPost(db.Model):  # many to one with company-type user account
    __tablename__ = 'jobpost'

    id = Column(Integer, primary_key=True)
    company_id = Column(ForeignKey('companyprofile.company_id'), nullable=False)
    job_title = Column(String(191), nullable=False)
    description = Column(String(191))
    created_timestamp = Column(DateTime, default=datetime.utcnow)

    company = relationship("CompanyProfile", back_populates="job_posts")

    def __repr__(self):
        return f"JobPost[by#{self.company_id}|{self.job_title}]"


@login.user_loader
def load_user(id):
    print(f"Loading user w/id {id}")
    return User.query.get(int(id))