from sqlalchemy import func

from app import db
from app.models import AccountTypes, User, SeekerProfile, JobPost


def count_rows(tbl):
    return db.session.query(func.count(tbl.id)).scalar()


def seeker_activeness_count():
    n_inactive = User.query.filter_by(account_type=AccountTypes.s, is_active=False).count()
    n_active = count_rows(SeekerProfile) - n_inactive
    return n_active, n_inactive


def job_activeness_count():
    n_inactive = JobPost.query.filter_by(active=False).count()
    n_active = count_rows(JobPost) - n_inactive
    return n_active, n_inactive
