from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Token(Base):
    __tablename__ = "token"

    id = Column(Integer, primary_key=True, index=True)
    mvs_token = Column(String)

