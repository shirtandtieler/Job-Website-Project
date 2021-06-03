import colorsys
import enum
import re
from datetime import datetime
from hashlib import md5
from operator import itemgetter
from typing import List, Tuple, Union
from zlib import crc32

from flask_login import UserMixin
from geopy.distance import geodesic
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, \
    Text, MetaData, DateTime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.sqltypes import LargeBinary, Numeric
from sqlalchemy_imageattach.entity import Image, image_attachment
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, geolocator

metadata = MetaData()

TINYGRAPH_THEMES = ["sugarsweets", "heatwave", "daisygarden", "seascape", "summerwarmth",
                    "bythepool", "duskfalling", "frogideas", "berrypie"]
TSKILL_TITLEIDS = None
BSKILL_TITLEIDS = None
ATTITUDE_TITLEIDS = None


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


class WorkTypes(enum.IntEnum):
    """
    An enumeration for declaring what work type is desired.
    Main 3 types are powers of two to allow for combinations.
    """
    full = 1
    part = 2
    contract = 4

    full_or_part = 3
    full_or_contract = 5
    part_or_contract = 6
    any = 7


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
    def to_tuples(sort_index=None, reverse=False) -> List[Tuple[str, int]]:
        global ATTITUDE_TITLEIDS
        if ATTITUDE_TITLEIDS is None:
            ATTITUDE_TITLEIDS = [(a.title, a.id) for a in Attitude.query.all()]

        if sort_index is None:
            return ATTITUDE_TITLEIDS
        else:
            return sorted(ATTITUDE_TITLEIDS, key=itemgetter(sort_index), reverse=reverse)

    @staticmethod
    def count() -> int:
        tups = Attitude.to_tuples()
        return len(tups)

    def to_dict(self):  # TODO do this with the others?
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
    def count() -> int:
        tups1 = Skill.to_tech_tuples()
        tups2 = Skill.to_biz_tuples()
        return len(tups1) + len(tups2)

    @staticmethod
    def to_tech_tuples(sort_index=None, reverse=False) -> List[Tuple[str, int]]:
        global TSKILL_TITLEIDS
        if TSKILL_TITLEIDS is None:
            TSKILL_TITLEIDS = [(s.title, s.id) for s in Skill.query.all() if s.is_tech()]

        if sort_index is None:
            return TSKILL_TITLEIDS
        else:
            return sorted(TSKILL_TITLEIDS, key=itemgetter(sort_index), reverse=reverse)

    @staticmethod
    def tech_count() -> int:
        tups = Skill.to_tech_tuples()
        return len(tups)

    @staticmethod
    def to_biz_tuples(sort_index=None, reverse=False) -> List[Tuple[str, int]]:
        global BSKILL_TITLEIDS
        if BSKILL_TITLEIDS is None:
            BSKILL_TITLEIDS = [(s.title, s.id) for s in Skill.query.all() if s.is_biz()]

        if sort_index is None:
            return BSKILL_TITLEIDS
        else:
            return sorted(BSKILL_TITLEIDS, key=itemgetter(sort_index), reverse=reverse)

    @staticmethod
    def biz_count() -> int:
        tups = Skill.to_biz_tuples()
        return len(tups)


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
    _job_searches = relationship("SeekerJobSearch", back_populates="_user")
    _seeker_searches = relationship("CompanySeekerSearch", back_populates="_user")

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
def load_user(id_):
    print(f"Loading user w/id {id_}")
    return User.query.get(int(id_))


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
    tagline = Column(String(100))
    summary = Column(String)

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
        _hashstr = re.sub(r"\W", "", self.name)
        # choose "random" attributes (theme and number of colors) based on lazy encoding
        _hashint = sum([ord(x) for x in self.name])
        _theme = TINYGRAPH_THEMES[_hashint % len(TINYGRAPH_THEMES)]
        _ncolors = 3 + (_hashint % 2)
        return f"http://www.tinygraphs.com/spaceinvaders/{_hashstr}?theme={_theme}&numcolors={_ncolors}&size={size}"

    def banner(self, dims=(100, 20)):
        _hashstr = re.sub(r"\W", "", self.name)
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
    work_wanted = Column(ENUM(WorkTypes), default=WorkTypes.any)
    remote_wanted = Column(Boolean, default=False)
    tagline = Column(String(100))
    summary = Column(String)
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
    def phone_formatted(self):
        if self.phone_number is None:
            return "Not provided"
        return re.sub(r"(\d*)(\d{3})(\d{3})(\d{4})", r"\1(\2) \3 - \4", self.phone_number)

    @property
    def work_wanted_list(self):
        wants = self.work_wanted.name.replace("_or_", "_").split("_")
        if WorkTypes.any.name in wants:
            wants = ["full", "part", "contract"]
        return wants

    @property
    def work_wanted_abbv(self):
        wants = self.work_wanted_list
        abbvs = []
        for w in wants:
            if w == 'full':
                abbvs.append("Ft")
            elif w == 'part':
                abbvs.append("Pt")
            else:
                abbvs.append("C")
        return abbvs

    @property
    def min_edu_level(self) -> int:
        """
        Converts the education experience to a single int representing the minimum qualifications held.
        This is one higher than the EducationLevel values (0 = no education, 1 = certification, etc.)
        """
        if len(self._history_edus) == 0:
            return 0
        # add one since allocating 0 for 'none'
        return int(max([e.education_lvl for e in self._history_edus])) + 1

    @property
    def min_edu_abbv(self) -> str:
        """
        Get's the abbreviated degree name of the min education level.
        """
        lvl = self.min_edu_level
        if lvl == 0:
            return "None"
        elif lvl == 1:
            return "Cert"
        elif lvl == 2:
            return "A.S."
        elif lvl == 3:
            return "B.S."
        elif lvl == 4:
            return "M.S."
        elif lvl == 5:
            return "D.S."

    @property
    def years_job_experience(self) -> int:
        """
        Calculates the number of years of job experience held.
        """
        return sum([job.years_employed for job in self._history_jobs])

    def get_tech_skills_levels(self):
        output = [(skr_skl._skill.title, int(skr_skl.skill_level)) for skr_skl in self._skills if
                  skr_skl._skill.is_tech()]
        output.sort(key=itemgetter(1), reverse=True)
        return output

    def get_tech_skills(self, only_max=False):
        skl_lvls = self.get_tech_skills_levels()
        if not skl_lvls:
            return []
        if not only_max:
            return [s[0] for s in skl_lvls]
        _max = skl_lvls[0][1]
        skls = []
        for skl, lvl in skl_lvls:
            if lvl < _max:
                break
            skls.append(skl)
        return skls

    def get_biz_skills_levels(self) -> List[Tuple[str, int]]:
        output = [(skr_skl._skill.title, int(skr_skl.skill_level)) for skr_skl in self._skills if
                  skr_skl._skill.is_biz()]
        output.sort(key=itemgetter(1), reverse=True)
        return output

    def get_biz_skills(self, only_max=False) -> List[Union[str,Tuple[str, int]]]:
        skl_lvls = self.get_biz_skills_levels()
        if not skl_lvls:
            return []
        if not only_max:
            return [s[0] for s in skl_lvls]
        _max = skl_lvls[0][1]
        skls = []
        for skl, lvl in skl_lvls:
            if lvl < _max:
                break
            skls.append(skl)
        return skls

    def get_attitudes(self) -> List[str]:
        return [skr_att._attitude.title for skr_att in self._attitudes]

    def is_within(self, distance_limit_mi, city, state) -> bool:
        if not self.city and not self.state:
            # always return true if user does not have a city or a state
            return True

        self_coords = LocationCoordinates.get(self.city, self.state)
        other_coords = LocationCoordinates.get(city, state)

        dist_mi = geodesic(self_coords, other_coords).miles
        return dist_mi <= distance_limit_mi

    def avatar(self, size=128):
        # convert email to random number between 0 and 1
        r01 = float(crc32(self._user.email.encode("utf-8")) & 0xffffffff) / 2 ** 32
        rand_bg_hex = "".join([hex(int(round(255 * x)))[2:] for x in colorsys.hsv_to_rgb(r01, 0.25, 1.0)])
        url = f"https://ui-avatars.com/api/?rounded=true&bold=true&color=00000" \
              f"&size={size}&background={rand_bg_hex}&name={self.first_name}+{self.last_name}"
        return url

    def to_dict(self) -> dict:
        """ Converts an instance of this class to a dictionary (e.g., for JSONifying it)"""
        d = dict()
        d['id'] = self.id
        d['name'] = self.full_name
        d['email'] = self._user.email
        d['phone'] = self.phone_number
        d['location'] = self.location
        ww = int(self.work_wanted)
        d['work_types'] = {
            'full': ww & 1 > 0,
            'part': ww & 2 > 0,
            'contract': ww & 4 > 0,
            'remote': self.remote_wanted}
        d['descriptions'] = {
            'tagline': self.tagline,
            'summary': self.summary}
        d['skills'] = {
            '__comment': 'Range: [1-5]',
            'tech': dict(self.get_tech_skills_levels()),
            'biz': dict(self.get_biz_skills_levels())}
        d['values'] = self.get_attitudes()
        d['history'] = {
            'education': [entry.to_dict() for entry in self._history_edus],
            'work': [entry.to_dict() for entry in self._history_jobs]}
        return d

    def encode_tech_skills(self) -> int:
        """
        Converts technical skills possessed to an integer.
        Only looks at whether the seeker added it to their profile.
        """
        # skill_id skill_level
        tskill_ids = [s.skill_id for s in self._skills if s._skill.is_tech()]
        enc = ['0' for _ in range(Skill.count())]
        for _id in tskill_ids:
            enc[_id - 1] = '1'
        return int(''.join(enc), base=2)

    def encode_biz_skills(self) -> int:
        """
        Converts business skills possessed to an integer.
        Only looks at whether the seeker added it to their profile.
        """
        # skill_id skill_level
        bskill_ids = [s.skill_id for s in self._skills if s._skill.is_biz()]
        enc = ['0' for _ in range(Skill.count())]
        for _id in bskill_ids:
            enc[_id - 1] = '1'
        return int(''.join(enc), base=2)

    def encode_attitudes(self) -> int:
        """
        Converts attitudes possessed to an integer.
        Only looks at whether the seeker added it to their profile.
        """
        # skill_id skill_level
        att_ids = [s.attitude_id for s in self._attitudes]
        enc = ['0' for _ in range(Attitude.count())]
        for _id in att_ids:
            enc[_id - 1] = '1'
        return int(''.join(enc), base=2)


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

    @property
    def education_lvl_abbv(self):
        lvl = self.education_lvl
        if lvl == 0:
            return "Certification"
        elif lvl == 1:
            return "A.S."
        elif lvl == 2:
            return "B.S."
        elif lvl == 3:
            return "M.S."
        elif lvl == 4:
            return "D.S."
        return "???"

    def to_dict(self) -> dict:
        d = dict()
        d['school'] = self.school
        d['type'] = self.education_lvl.name
        d['field'] = self.study_field
        return d


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

    def to_dict(self) -> dict:
        d = dict()
        d['title'] = self.job_title
        d['years'] = self.years_employed
        return d


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

    def get_skills_data(self, type_='all', name=False) -> List[Tuple[Union[str, int], int, int]]:
        """
        Gets a list of skills, where each entry contains:
            1. the id or name of the skill (depends on the value of `name`)
            2. the minimum skill level (1-5)
            3. the importance level (0-5)
        Can filter skills to either [t]ech, [b]iz, or [a]ll
        """
        matches_type = lambda skl: type_ == 'all' or \
                                   (type_.startswith('t') and skl._skill.is_tech()) or \
                                   (type_.startswith('b') and skl._skill.is_biz())
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
    jobpost_id = Column(Integer, ForeignKey('jobpost.id', ondelete="CASCADE"), nullable=False)
    attitude_id = Column(Integer, ForeignKey('attitude.id', ondelete="CASCADE"), nullable=False)
    importance_level = Column(ENUM(ImportanceLevel), default=ImportanceLevel.none)

    _job_post = relationship("JobPost", back_populates="_attitudes")
    _attitude = relationship("Attitude", back_populates="_job_posts")

    def __repr__(self):
        return f"JobPost[{self.jobpost_id}]-Attitude[{self.attitude_id}|{self.importance_level}]"


##### SEARCHES #####
class CompanySeekerSearch(db.Model):
    __tablename__ = 'company_seeker_search'
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    label = Column(String, nullable=False)
    query = Column(String, nullable=False)

    _user = relationship("User", back_populates="_seeker_searches")


class SeekerJobSearch(db.Model):
    __tablename__ = 'seeker_job_search'
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    label = Column(String, nullable=False)
    query = Column(String, nullable=False)

    _user = relationship("User", back_populates="_job_searches")


##### LOGGING/CACHE #####
class LocationCoordinates(db.Model):
    """
    This table contains a mapping between a location string to the coordinates of that location.
    It contains static functions to convert a given city/state to the expected format and to 'get' coordinates
        (which will attempt to first retrieve from the table, then query the geolocator if not present).
    Locations are in the format: `X, Y USA` where X is the city name and Y is the state's 2 letter abbreviation.
    """
    __tablename__ = 'location_coordinates'
    location = Column(String, nullable=False, primary_key=True)
    latitude = Column(Numeric)
    longitude = Column(Numeric)

    @staticmethod
    def to_location(city: str = None, state: str = None) -> str:
        """
        Converts a city and state (both optional) to the key expected by this table.
        """
        if city is None and state is None:
            return "USA"
        elif city is None or state is None:
            return f"{city}{state}, USA"
        return f"{city}, {state} USA"

    @staticmethod
    def get(city: str = None, state: str = None) -> Tuple[float, float]:
        loc_id = LocationCoordinates.to_location(city, state)
        row = LocationCoordinates.query.get(loc_id)
        if row is None:
            # not present, create then return
            loc_obj = geolocator.geocode(loc_id)
            row = LocationCoordinates(location=loc_id, latitude=loc_obj.latitude, longitude=loc_obj.longitude)
            db.session.add(row)
            db.session.commit()
        return row.latitude, row.longitude
