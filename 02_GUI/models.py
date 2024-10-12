from sqlalchemy import Column, DateTime,Text,Integer,Interval,ForeignKey,Float
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import DeclarativeBase, sessionmaker

Session = sessionmaker()

class Base(DeclarativeBase):
    pass

class teams(Base):
    __tablename__ = "teams"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(Text,nullable=False,index=True)

class challenges(Base):
    __tablename__ = "challenges"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(Text,nullable=False)
    penalty = Column(Float,nullable=False)

class challenges_data(Base):
    __tablename__ = "challenges_data"
    id            = Column(Integer,primary_key=True,index=True)
    tea_id        = Column(Integer,ForeignKey("teams.id"),nullable=False)
    cmp_id        = Column(Integer,ForeignKey("challenges.id"),nullable=False)
    attempt_nr    = Column(Integer,nullable=False)
    starttime     = Column(DATETIME(fsp=6))
    stoptime      = Column(DATETIME(fsp=6))
    timepenalty   = Column(Float)
    time          = Column(Float,nullable=False)

class challenges_best_attempts(Base):
    __tablename__ = "challenges_best_attempts"
    id           = Column(Integer,primary_key=True,index=True)
    challenge_id = Column(Integer, index=True)
    team_id      = Column(Integer, index=True)
    time         = Column(Float,nullable=False)

class leaderboard(Base):
    __tablename__ = "leaderboard"
    id      = Column(Integer,primary_key=True,index=True)
    team_id = Column(Integer, index=True)
    points  = Column(Integer, index=True)

class raw_data(Base):
    __tablename__ = "raw_data"
    id = Column(Integer,primary_key=True,index=True)
    esp_id = Column(Text,nullable=False)
    timestamp = Column(DATETIME(fsp=6),nullable=False)

