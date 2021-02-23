from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.Token).filter(models.Token.id == user_id).first()

def store_token(db: Session, mvs_token: str):
    db_user = models.Token(mvs_token=mvs_token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_tokens(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Token).offset(skip).limit(limit).all()
