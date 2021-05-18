from datetime import datetime
from hashlib import md5

from flask import url_for
from sqlalchemy.sql.elements import Null
from sqlalchemy import Boolean, CheckConstraint, Column, Date, Enum, ForeignKey, Integer, SmallInteger, String, \
    Sequence, Table, Text, UniqueConstraint, text, MetaData, DateTime
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.sql.sqltypes import LargeBinary, SMALLINT, TIMESTAMP
from sqlalchemy_imageattach.entity import Image, image_attachment
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

metadata = MetaData()

account_types = Enum('Seeker', 'Company', 'Admin', name='account_types')
skill_types = Enum('tech', 'biz', name='skill_types')
skill_levels = Enum('1','2','3','4','5', name='skill_levels')
job_lables = Enum("Want to apply", "Considering to apply", "Will not apply", name='job_labels')

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
                
    def update(self):
        if self.is_active == True:
            self.last_login = datetime.utcnow


class CompanyPicture(db.Model, Image):
    __tablename__ = 'companypicture'
    user_id = Column(Integer, ForeignKey('companyprofile.id'), primary_key=True)
    user = relationship('CompanyProfile')


class CompanyProfile(db.Model):  # one to one with company-type user account
    __tablename__ = 'companyprofile'

    id = Column(Integer, primary_key=True)
    company_id = Column('company_id', ForeignKey('useraccount.id'), nullable=False, unique=True)
    name = Column(String(191), server_default=text("NULL"))
    city = Column(String(191), server_default=text("NULL"))
    state = Column(String(2), server_default=text("NULL"))
    website = Column(String(191), server_default=text("NULL"))
    picture = image_attachment('CompanyPicture')
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
    resume = Column(LargeBinary, nullable=False)
    picture = image_attachment('SeekerPicture')

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


class SeekerPicture(db.Model, Image):
    __tablename__ = 'seekerpicture'
    user_id = Column(Integer, ForeignKey('seekerprofile.id'), primary_key=True)
    user = relationship('SeekerProfile')


class JobPost(db.Model):  # many to one with company-type user account
    __tablename__ = 'jobpost'

    id = Column(Integer, primary_key=True)
    company_id = Column(ForeignKey('companyprofile.company_id'), nullable=False)
    job_title = Column(String(191), nullable=False)
    description = Column(String(191))
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, nullable=False)
    company = relationship("CompanyProfile", back_populates="job_posts")

    def __repr__(self):
        return f"JobPost[by#{self.company_id}|{self.job_title}]"


class SeekerHistoryEducation(db.Model):
    __tablename__='SeekerHistoryEducation'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    education_lvl = Column(String, nullable=False)
    study_field = Column(String, nullable=False)
    school = Column(String, nullable=False)
    city = Column(String, default=Null)
    state_abv = Column(String, default=Null)
    active_enrollment = Column(SMALLINT, default=Null)
    start_date = Column(Date, default=Null)
    
    seekr = relationship('useraccount', back_populates= 'SeekerHistoryEducation')

class SeekerHistoryJob(db.Model):
    __tablename__='SeekerHistoryJob'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    city = Column(String(191), server_default=text("NULL"))
    state = Column(String(2), server_default=text("NULL"))
    
    seekr = relationship('useraccount', back_populates= 'SeekerHistoryJob')
    
class SeekerSkill(db.Model):
    __tablename__='SeekerSkill'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    seekr = relationship('useraccount', back_populates= 'SeekerSkill')
    skill_id = Column(Integer, ForeignKey('Skill.id'),nullable=False)
    skill = relationship('Skill', back_populates= 'SeekerHistoryJob')
    skill_level = Column(Enum(skill_levels),nullable=False)
     
class Applied(db.Model):
    __tablename__='Applied'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    seekr = relationship('useraccount', back_populates= 'Applied')
    job_id = Column(Integer, ForeignKey('jobpost.id'),nullable=False)
    jobpost = relationship('Skill', back_populates= 'Applied')
    
class Bookmark(db.Model):
    __tablename__='Bookmarks'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    seekr = relationship('useraccount', back_populates= 'Bookmarks')
    job_id = Column(Integer, ForeignKey('jobpost.id'),nullable=False)
    jobpost = relationship('Skill', back_populates= 'Bookmarks')
    
class SeekerSearch(db.Model):
    __tablename__='SeekerSearch'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    seekr = relationship('useraccount', back_populates= 'SeekerSearch')
    job_id = Column(Integer, ForeignKey('jobpost.id'),nullable=False)
    jobpost = relationship('Skill', back_populates= 'SeekerSearch')
    label = Column(job_lables, nullable=False)
        
@login.user_loader
def load_user(id):
    print(f"Loading user w/id {id}")
    return User.query.get(int(id))