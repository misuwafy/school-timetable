from sqlalchemy import Column, Integer, String, Boolean, JSON
from database import Base


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    maxPeriodsPerDay = Column(Integer, default=7)
    isBlockHead = Column(Boolean, default=False)
    headOfBlock = Column(String, default="")


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, default="")
    head = Column(String, default="")


class SchoolClass(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    divisions = Column(JSON, nullable=False)
    block = Column(String, default="")
    classTeacher = Column(String, default="")
    subjects = Column(JSON, nullable=False)


class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(JSON, nullable=False)
