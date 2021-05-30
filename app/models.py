import colorsys
import re
from datetime import datetime
from hashlib import md5
from random import random
from typing import List, Tuple, Union

from sqlalchemy.sql.elements import Null
from flask import url_for
from sqlalchemy.sql.elements import Null
from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, SmallInteger, String, \
    Sequence, Table, Text, UniqueConstraint, text, MetaData, DateTime
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.sql.sqltypes import LargeBinary, SMALLINT, TIMESTAMP
from sqlalchemy_imageattach.entity import Image, image_attachment
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql.sqltypes import SMALLINT, TIMESTAMP
import enum
from sqlalchemy.dialects.postgresql import ENUM

metadata = MetaData()

TINYGRAPH_THEMES = ["sugarsweets", "heatwave", "daisygarden", "seascape", "summerwarmth",
                    "bythepool", "duskfalling", "frogideas", "berrypie"]

class AccountTypes(enum.Enum):
    """
    An enumeration for identifying the account type of a user: seeker, company, or admin.
    """
    s = 'Seeker'
    c = 'Company'
    a = 'Admin'


class SkillTypes(enum.Enum):
    """
    An enumeration for identifying which type a given skill is: technical or business.
    """
    t = 'Tech'
    b = 'Biz'


class SkillLevels(enum.IntEnum):
    """
    An enumeration for declaring how experienced one is in a given context.
    Used by seekers in relation to their skills.
    """
    novice = 1
    familiar = 2
    competent = 3
    proficient = 4
    expert = 5


class ImportanceLevel(enum.IntEnum):
    """
    An enumeration for declaring an importance level of an attribute in some context.
    Used in job posts for companies to declare how important it is for a seeker to have some skill or attitude.
    """
    none = 0
    vlow = 1
    low = 2
    mid = 3
    high = 4
    vhigh = 5


class EducationLevel(enum.IntEnum):
    """
    An enumeration for declaring education levels.
    Used in seeker profiles for declaring their certification or degrees.
    """
    certification = 0
    associate = 1
    bachelor = 2
    master = 3
    doctoral = 4


##### SHARED TYPES #####

## TODO add admin profile (will service as the page with the cards for actions)

class Attitude(db.Model):
    """
    Represents a cultural attitude.
    """
    __tablename__ = 'attitude'

    id = Column(Integer, primary_key=True)
    title = Column(String(191), nullable=False, unique=True)

    _seekers = relationship("SeekerAttitude", back_populates="_attitude")
    _job_posts = relationship("JobPostAttitude", back_populates="_attitude")

    def __repr__(self):
        return f"Attitude[{self.title}]"

    @staticmethod
    def get_attitude_names():
        return [[a.title for a in Attitude.query.all()]]

    def to_dict(self):  ## TODO do this with the others
        return {
            "title": self.title,
            "_seekers": [x.id for x in self._seekers],
            "_job_posts": [x.id for x in self._job_posts]
        }


class Skill(db.Model):
    """
    Represents a technical or business skill.
    """
    __tablename__ = 'skill'

    id = Column(Integer, primary_key=True)
    title = Column(String(191), nullable=False, unique=True)
    type = Column(ENUM(SkillTypes), nullable=False)

    _seekers = relationship("SeekerSkill", back_populates="_skill")
    _job_posts = relationship("JobPostSkill", back_populates="_skill")

    def __repr__(self):
        return f"{self.type.name.capitalize()}Skill[{self.title}]"

    def is_tech(self):
        return self.type == SkillTypes.t

    def is_biz(self):
        return self.type == SkillTypes.b

    @staticmethod
    def get_skill_names():
        return [[s.title for s in Skill.query.all()]]


class UserPicture(db.Model, Image):
    __tablename__ = 'user_picture'

    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)

    _user = relationship('User', back_populates="_picture")


class User(UserMixin, db.Model):
    """
    Represents an account with the website (whether seeker, company, or admin).
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    account_type = Column(ENUM(AccountTypes), nullable=False)
    email = Column(String(191), nullable=False, unique=True)
    password = Column(String(191), nullable=False)
    is_active = Column(Boolean, default=True)
    join_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=False, default=datetime.utcnow)

    _picture = image_attachment("UserPicture", uselist=False, back_populates="_user")
    _company = relationship("CompanyProfile", uselist=False, back_populates="_user")
    _seeker = relationship("SeekerProfile", uselist=False, back_populates="_user")

    def __repr__(self):
        status = ("" if self.is_active else "Non") + "Active"
        return f"{status}{self.account_type}User[{self.email}]"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def update(self):
        if self.is_active:
            self.last_login = datetime.utcnow


@login.user_loader
def load_user(id):
    print(f"Loading user w/id {id}")
    return User.query.get(int(id))

##### PROFILES ######

class CompanyProfile(db.Model):  # one to one with company-type user account
    """
    Table of profile information for Companies.
    One to one with user account (of type company).

    """
    __tablename__ = 'company_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', ForeignKey('user.id', ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String(191), nullable=False)
    city = Column(String(191))
    state = Column(String(2))
    website = Column(String(191))

    # TODO add logo (and banner?) then replace instances that use 'blue_company' image
    # TODO add slogan or description?

    _user = relationship("User", back_populates="_company")
    _job_posts = relationship("JobPost", back_populates="_company")

    def __repr__(self):
        return f"CompanyProfile[{self.name}]"

    @property
    def location(self):
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        elif self.city or self.state:
            return f"{self.city}{self.state}"
        else:
            return "USA"

    @validates('company_id')
    def validate_account(self, key, company_id):
        acct = User.query.filter_by(id=company_id).first()
        if acct is None:
            raise ValueError(f"No account w/id={company_id}")
        if acct.account_type != AccountTypes.c:
            raise ValueError(f"Account type is not a Company")
        return company_id

    def avatar(self, size=128):
        _hashstr = re.sub("\W", "", self.name)
        # choose "random" attributes (theme and number of colors) based on lazy encoding
        _hashint = sum([ord(x) for x in self.name])
        _theme = TINYGRAPH_THEMES[_hashint % len(TINYGRAPH_THEMES)]
        _ncolors = 3 + (_hashint % 2)
        return f"http://www.tinygraphs.com/spaceinvaders/{_hashstr}?theme={_theme}&numcolors={_ncolors}&size={size}"

    def banner(self, dims=(100, 20)):
        _hashstr = re.sub("\W", "", self.name)
        # choose "random" attributes (theme and number of colors) based on lazy encoding
        _hashint = sum([ord(x) for x in self.name])
        _theme = TINYGRAPH_THEMES[_hashint % len(TINYGRAPH_THEMES)]
        _ncolors = 3 + (_hashint % 2)
        _ntris = 40 + (_hashint % 20)
        return f"https://www.tinygraphs.com/isogrids/banner/random/gradient?w={dims[0]}&h={dims[1]}&xt={_ntris}&theme={_theme}&numcolors={_ncolors}"


class SeekerProfile(db.Model):
    """
    Table of profile information for Seekers.
    One to one with user account (of type seeker).
    One to many with a seeker skill.
    One to many with a seeker attitude.
    One to many with an entry for education history.
    One to many with an entry for a job history.
    One to many with a job applied to.
    One to many with a job bookmarked.
    """
    __tablename__ = 'seeker_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', ForeignKey('user.id'), nullable=False, unique=True)
    first_name = Column(String(191), nullable=False)
    last_name = Column(String(191), nullable=False)
    phone_number = Column(String(10))
    city = Column(String(191))
    state = Column(String(2))
    resume = Column(LargeBinary)

    _user = relationship("User", back_populates="_seeker")
    _skills = relationship("SeekerSkill", back_populates="_seeker")
    _attitudes = relationship("SeekerAttitude", back_populates="_seeker")
    _history_edus = relationship("SeekerHistoryEducation", back_populates="_seeker")
    _history_jobs = relationship("SeekerHistoryJob", back_populates="_seeker")
    _applications = relationship("SeekerApplication", back_populates="_seeker")
    _bookmarks = relationship('SeekerBookmark', back_populates='_seeker')

    def __repr__(self):
        return f"SeekerProfile[{self.first_name}{self.last_name}]"

    @validates('seeker_id')
    def validate_account(self, key, seeker_id):
        acct = User.query.filter_by(id=seeker_id).first()
        if acct is None:
            raise ValueError(f"No account w/id={seeker_id}")
        if acct.account_type != AccountTypes.s:
            raise ValueError(f"Account type is not a Seeker")
        return seeker_id

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def location(self):
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        elif self.city or self.state:
            return f"{self.city}{self.state}"
        else:
            return "USA"

    @property
    def tag_lines(self):
        """ Return a list of things this seeker can boast about."""
        lines = []
        # get a line about a number of their highest skills
        skill_highest_lvl, skill_highest_count = 0, 0
        for skl in self._skills:
            lvl = int(skl.skill_level)
            if lvl > skill_highest_lvl:
                skill_highest_lvl = lvl
                skill_highest_count = 1
            elif lvl == skill_highest_lvl:
                skill_highest_count += 1
        if skill_highest_lvl > 0:  # make sure seeker has some skills
            skill_lvl = str(SkillLevels(skill_highest_lvl))
            lvl_name = skill_lvl[skill_lvl.index('.')+1:].capitalize()
            s = "skills" if skill_highest_count > 1 else "skill"
            lines.append(f"{lvl_name} in {skill_highest_count} {s}")
        # get a line about their past experience
        if len(self._history_edus) > 0 and len(self._history_jobs) > 0:
            total_years = sum([job.years_employed for job in self._history_jobs])
            d = "degrees" if len(self._history_edus) > 1 else "degree"
            y = "years" if total_years > 1 else "year"
            lines.append(f"Holds {len(self._history_edus)} {d} and {total_years} {y} of job experience.")
        elif len(self._history_edus) > 0:
            d = "degrees" if len(self._history_edus) > 1 else "degree"
            lines.append(f"Holds {len(self._history_edus)} {d}")  # TODO maybe add highest level/give example?
        elif len(self._history_jobs) > 0:
            total_years = sum([job.years_employed for job in self._history_jobs])
            y = "years" if total_years > 1 else "year"
            lines.append(f"Has {total_years} {y} of job experience.")  # TODO maybe add example title?
        return lines

    def avatar(self, size=128):
        rand_bg_hex = "".join([hex(int(round(255*x)))[2:] for x in colorsys.hsv_to_rgb(random(), 0.25, 1.0)])
        url = f"https://ui-avatars.com/api/?rounded=true&bold=true&color=00000" \
              f"&size={size}&background={rand_bg_hex}&name={self.first_name}+{self.last_name}"
        return url



class SeekerSkill(db.Model):
    """
    Table of connections between seeker and skill.
    Many to one with a seeker's profile.
    Many to one with a skill.
    """
    __tablename__ = 'seeker_skill'

    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey('skill.id', ondelete="CASCADE"), nullable=False)
    skill_level = Column(ENUM(SkillLevels), nullable=False)

    _seeker = relationship("SeekerProfile", back_populates="_skills")
    _skill = relationship("Skill", back_populates="_seekers")

    def __repr__(self):
        return f"Seeker{self.seeker_id}-Skill{self.skill_id}@{self.skill_level}"


class SeekerAttitude(db.Model):
    """
    Table of connections between seeker and attitude.
    Many to one with a seeker's profile.
    Many to many with an attitude.
    """
    __tablename__ = 'seeker_attitude'

    id = Column(Integer, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    attitude_id = Column(Integer, ForeignKey('attitude.id', ondelete="CASCADE"), nullable=False)

    _seeker = relationship('SeekerProfile', back_populates='_attitudes')
    _attitude = relationship('Attitude', back_populates="_seekers")

    def __repr__(self):
        return f"Seeker[{self.seeker_id}]-Attitude[{self.attitude_id}]"


class SeekerHistoryEducation(db.Model):
    """
    Table of connections between a seeker and a past educational experience.
    Many to one with a seeker's profile.
    """
    __tablename__ = 'seeker_history_education'

    id = Column(Integer, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    school = Column(String, nullable=False)
    education_lvl = Column(ENUM(EducationLevel), nullable=False)
    study_field = Column(String, nullable=False)

    _seeker = relationship('SeekerProfile', back_populates='_history_edus')

    def __repr__(self):
        return f"Seeker[{self.seeker_id}]-EduExp[{self.education_lvl}:{self.study_field}@{self.school}]"


class SeekerHistoryJob(db.Model):
    """
    Table of connections between a seeker and a past job experience.
    Many to one with a seeker's profile.
    """
    __tablename__ = 'seeker_history_job'

    id = Column(Integer, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    job_title = Column(String(191))
    years_employed = Column(Integer)

    _seeker = relationship('SeekerProfile', back_populates='_history_jobs')

    def __repr__(self):
        return f"Seeker[{self.seeker_id}]-JobExp[{self.job_title}:{self.years_employed} years]"


class SeekerApplication(db.Model):
    """
    Table of connections between a seeker and jobs applied to.
    Many to one with a seeker's profile.
    One to one with a job post.
    """
    __tablename__ = 'seeker_application'

    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey('jobpost.id', ondelete="CASCADE"), nullable=False)

    _seeker = relationship('SeekerProfile', back_populates='_applications')
    _job_post = relationship('JobPost', back_populates='_seekers_applied')

    def __repr__(self):
        return f"Seeker[{self.seeker_id}]-Application[{self.job_id}]"


class SeekerBookmark(db.Model):
    """
    Table of connections between a seeker and jobs bookmarked.
    Many to one with a seeker's profile.
    One to one with a job post.
    """
    __tablename__ = 'seeker_bookmark'

    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker_profile.id', ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey('jobpost.id', ondelete="CASCADE"), nullable=False)

    _seeker = relationship('SeekerProfile', back_populates='_bookmarks')
    _job_post = relationship('JobPost', back_populates='_seekers_bookmarked')

    def __repr__(self):
        return f"Seeker[{self.seeker_id}]-Bookmark[{self.job_id}]"


##### JOB POST #####

class JobPost(db.Model):
    """
    Table of job posts by a company.
    Many to one with a company profile.
    One to many with a job post skill.
    One to many with a job post attitude.
    """
    __tablename__ = 'jobpost'

    id = Column(Integer, primary_key=True)
    company_id = Column(ForeignKey('company_profile.id'), nullable=False)
    job_title = Column(String(191), nullable=False)
    city = Column(String(191))
    state = Column(String(2))
    description = Column(Text)
    is_remote = Column(Boolean, default=False)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    created_timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    _company = relationship("CompanyProfile", back_populates="_job_posts")
    _skills = relationship("JobPostSkill", back_populates="_job_post")
    _attitudes = relationship("JobPostAttitude", back_populates="_job_post")
    _seekers_applied = relationship("SeekerApplication", back_populates="_job_post")
    _seekers_bookmarked = relationship("SeekerBookmark", back_populates="_job_post")

    def __repr__(self):
        return f"JobPost[by#{self.company_id}|{self.job_title}]"

    @property
    def company(self):
        return self._company.name

    @property
    def location(self):
        if self.city and self.state:
            loc = f"{self.city}, {self.state}"
        elif self.city or self.state:
            loc = f"{self.city}{self.state}"
        else:
            loc = "USA"

        if self.is_remote:
            loc += " (remote available)"
        return loc

    @property
    def expected_salary(self):
        if self.salary_min and self.salary_max:
            sal = f"Between ${self.salary_min} and ${self.salary_max}"
        elif self.salary_min:
            sal = f"${self.salary_min}+"
        elif self.salary_max:
            sal = f"Up to ${self.salary_max}"
        else:
            sal = f"Salary depends on experience"
        return sal

    def n_tech_skills(self):
        n = 0
        for skl in self._skills:
            if skl._skill.is_tech():
                n += 1
        return n

    def n_biz_skills(self):
        n = 0
        for skl in self._skills:
            if skl._skill.is_biz():
                n += 1
        return n

    def n_skills(self):
        return len(self._skills)

    def get_skills_data(self, type='all', name=False) -> List[Tuple[Union[str, int], int, int]]:
        """
        Gets a list of skills, where each entry contains:
            1. the id or name of the skill (depends on the value of `name`)
            2. the minimum skill level (1-5)
            3. the importance level (0-5)
        Can filter skills to either [t]ech, [b]iz, or [a]ll
        """
        matches_type = lambda skl: type == 'all' or \
                                   (type.startswith('t') and skl._skill.is_tech()) or \
                                   (type.startswith('b') and skl._skill.is_biz())
        return [(s._skill.title if name else s.skill_id, s.skill_level_min, s.importance_level)
                for s in self._skills if matches_type(s)]

    def n_attitudes(self):
        return len(self._attitudes)

    def get_attitude_data(self, name=False) -> List[Tuple[Union[str, int], int]]:
        """
        Get a list of attitudes, where each entry contains:
            1. the id or name of the attitude (depends on the value of `name`)
            2. the importance level (0-5)
        """
        return [(a._attitude.title if name else a.attitude_id, a.importance_level)
                for a in self._attitudes]


class JobPostSkill(db.Model):
    """
    Table of entries representing a skill requirement in a job post.
    Many to one with a job post.
    Many to many with a skill.
    """
    __tablename__ = 'jobpost_skill'

    id = Column(Integer, nullable=False, primary_key=True)
    jobpost_id = Column(Integer, ForeignKey('jobpost.id', ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey('skill.id', ondelete="CASCADE"), nullable=False)
    skill_level_min = Column(ENUM(SkillLevels), default=SkillLevels.novice)
    importance_level = Column(ENUM(ImportanceLevel), default=ImportanceLevel.none)

    _job_post = relationship("JobPost", back_populates="_skills")
    _skill = relationship("Skill", back_populates="_job_posts")

    def __repr__(self):
        return f"JobPost[{self.jobpost_id}]-Skill[{self.skill_id}|{self.skill_level_min}|{self.importance_level}]"


class JobPostAttitude(db.Model):
    """
    Table of entries representing an attitude requirement in a job post.
    Many to one with a job post.
    Many to many with an attitude.
    """
    __tablename__ = 'jobpost_attitude'

    id = Column(Integer, nullable=False, primary_key=True)
    jobpost_id = Column(Integer, ForeignKey('jobpost.id', ondelete="CASCADE"), nullable= False)
    attitude_id = Column(Integer, ForeignKey('attitude.id', ondelete="CASCADE"), nullable=False)
    importance_level = Column(ENUM(ImportanceLevel), default=ImportanceLevel.none)

    _job_post = relationship("JobPost", back_populates="_attitudes")
    _attitude = relationship("Attitude", back_populates="_job_posts")

    def __repr__(self):
        return f"JobPost[{self.jobpost_id}]-Attitude[{self.attitude_id}|{self.importance_level}]"


##### SEARCHES #####
'''
class SeekerSearch(db.Model):
    __tablename__='seeker_search'
    id = Column(Integer, nullable=False, primary_key=True)
    seeker_id = Column(Integer, ForeignKey('seeker.id'),nullable=False)
    job_id = Column(Integer, ForeignKey('jobpost.id'),nullable=False)
    label = Column(job_lables, nullable=False)

    user = relationship('User')
    skill = relationship('Skill', back_populates= 'SeekerSearch')
'''

'''

class CompanySeekerSearch(db.Model):
    __tablename__ = 'companyseekersearch'

    id = Column(Integer, nullable=False, primary_key=True)

    seekrid = Column(Integer, ForeignKey('seekerprofile.seeker_id'), nullable=False)
    seekr_city = Column(Integer, ForeignKey('seekerprofile.city'), nullable=False)
    seekr_state = Column(Integer, ForeignKey('seekerprofile.state'), nullable=False)
    seekr_skill = Column(ForeignKey('skill.title'), default='Not update yet')
    seekr_type = Column(ForeignKey('skill.type'), default='Not update yet')
    seekr_attitude = Column(ForeignKey('attitude.title'), nullable=False)
    company = relationship("CompanyProfile", back_populates="companyseekersearch")
'''

