from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum
from sqlalchemy.sql.elements import Null
from sqlalchemy.sql.expression import false, null
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.sql.schema import CheckConstraint
from sqlalchemy.sql.sqltypes import Boolean, Date, SMALLINT, TIMESTAMP
import sqlalchemy.types as types

db_string = "postgresql://postgres:password@localhost:5432/Handshake2"
engine = create_engine(db_string, echo =True)

Base = declarative_base()

class Skill_Types(enum.Enum):
    TECH = 1
    BIZ = 2

class Account_Types(enum.Enum):
    Seeker = 1
    Company = 2
    Admin = 3

class Skill_Level(enum.Enum):
    One =1 
    Two = 2
    Three = 3
    Four = 4
    Five = 5

class Importance_Level(enum.Enum):
    Required = 1
    Two = 2
    Three = 3
    Prefered = 4
    Five = 5
    Six = 6
    Optional = 7

i = 0
def mydefault():
    global i
    i += 1
    return i

class Attitude(Base):
    __tablename__ = 'Attitude'
    
    id = Column(Integer,nullable=False, primary_key=True)
    title = Column(String,nullable=False)

class Skill(Base):
    __tablename__ = 'Skill'
    
    id = Column(Integer, nullable=False, primary_key=True)
    title = Column(String, nullable=False)
    skill_type = Column(Enum(Skill_Types), nullable=False)
    
class UserAccount(Base):
    __tablename__ = 'UserAccount'
    
    id = Column(Integer, nullable=False, primary_key=True, unique=True)
    account_type = Column(Enum(Account_Types), nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable= False)
        
class UserActivity(Base):
    __tablename__ = 'UserActivity'
    
    user_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False, primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True)
    join_date = Column(TIMESTAMP, nullable=False, default=current_timestamp)
    last_login = Column(TIMESTAMP, nullable=False, default=current_timestamp)
    user = relationship("UserAccount", back_populates="UserActivity")
    
class CompanyProfile(Base):
    __tablename__ = 'CompanyProfile'
    
    company_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False, primary_key=True)
    company_name = Column(String, default=Null)
    city = Column(String, default=Null)
    state_abv = Column(String, default=Null)
    zip_code = Column(String, default=Null)
    website = Column(String, default=Null)
    user = relationship("UserAccount", back_populates="CompanyProfile")

class SeekerProfile(Base):
    __tablename__ = 'SeekerProfile'
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False, primary_key=True)
    contact_email = Column(String, nullable=False)
    first_name = Column(String, default=Null)
    last_name = Column(String, default=Null)
    contact_phone = Column(Integer, default=Null)
    city = Column(String, default=Null)
    state_abv = Column(String, default=Null)
    zip_code = Column(String, default=Null)
    user = relationship("UserAccount", back_populates="SeekerProfile")
    
class SeekerHistoryEducation(Base):
    __tablename__='SeekerHistoryEducation'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('UserAccount.id'),nullable=False)
    education_lvl = Column(String, nullable=False)
    study_field = Column(String, nullable=False)
    school = Column(String, nullable=False)
    city = Column(String, default=Null)
    state_abv = Column(String, default=Null)
    active_enrollment = Column(SMALLINT, default=Null)
    start_date = Column(Date, default=null)
    
    
Base.metadata.create_all(engine)