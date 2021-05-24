# TODO add functions to create/update/get entries in database related to users or their account/profile

from app import db
from app.models import AccountTypes
from app.models import User, CompanyProfile, SeekerProfile


def new_company(email, password, join_date=None, profile_data=None):
    """
    Adds a new Company to the database.
    profile data can a dict containing:
        name
        city
        state
        website
    """
    user = User()
    user.account_type = AccountTypes.c
    user.email = email
    user.set_password(password)
    if join_date is not None:
        user.join_date = join_date

    # before the profile can be created, it needs to committed
    # (as that's when the id field is generated)
    db.session.add(user)
    db.session.commit()
    if profile_data is not None:
        profile = CompanyProfile()
        profile.user_id = user.id
        profile.name = profile_data.get("name", "COMPANY")
        profile.city = profile_data.get("city", None)
        profile.state = profile_data.get("state", None)
        profile.website = profile_data.get("website", None)
        db.session.add(profile)
        db.session.commit()


def new_seeker(email, password, join_date=None, profile_data=None):
    """
    Adds a new Seeker to the database.
    `profile` could be a dict containing:
        first_name
        last_name
        phone_number
        city
        state
    """
    user = User()
    user.account_type = AccountTypes.s
    user.email = email
    user.set_password(password)
    if join_date is not None:
        user.join_date = join_date

    # before the profile can be created, it needs to committed
    # (as that's when the id field is generated)
    db.session.add(user)
    db.session.commit()
    if profile_data is not None:
        profile = SeekerProfile()
        profile.user_id = user.id
        profile.first_name = profile_data.get("first_name", "FIRST")
        profile.last_name = profile_data.get("last_name", "LAST")
        profile.phone_number = profile_data.get("phone_number", None)
        profile.city = profile_data.get("city", None)
        profile.state = profile_data.get("state", None)
        db.session.add(profile)
        db.session.commit()

