from sqlalchemy import Column, Integer, String, Boolean, JSON, Text
from database import Base


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    maxPeriodsPerDay = Column(Integer, default=7)
    isBlockHead = Column(Boolean, default=False)
    headOfBlock = Column(String(200), default="")
    unavailable = Column(JSON, default=[])


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(String(500), default="")
    head = Column(String(200), default="")


class SchoolClass(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    divisions = Column(JSON, nullable=False)
    block = Column(String(200), default="")
    classType = Column(String(200), default="")
    classTeacher = Column(String(200), default="")
    subjects = Column(JSON, nullable=False)


class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(JSON, nullable=False)
