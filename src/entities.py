from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True) # PK
    login = Column(String(64), unique=True)
    password = Column(String(72))
    # relationships
    sessions = relationship("Session", back_populates="account")
    links = relationship("Link", back_populates="owner")
class Session(Base):
    __tablename__ = 'session'
    key = Column(String(256), unique=True, primary_key=True) #PK
    user_id = Column(Integer, ForeignKey('user.id')) # FK
    created_at = Column(Date)
    expires_at = Column(Date)
    # relationships
    account = relationship("User", back_populates="sessions")
class Link(Base):
    __tablename__ = "link"
    key = Column(String(256), unique=True, primary_key=True) #PK
    user_id = Column(Integer, ForeignKey('user.id')) # FK
    path = Column(Text)
    # relationships
    owner = relationship("User", back_populates="links")