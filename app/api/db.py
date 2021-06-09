from sqlalchemy import func

from app import db


def count_rows(tbl):
    return db.session.query(func.count(tbl.id)).scalar()
