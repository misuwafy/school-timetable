from sqlalchemy import Column, Integer, String, Boolean, JSON
from database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    max_periods_per_day = Column(Integer, default=7)
    is_block_head = Column(Boolean, default=False)
    head_of_block = Column(String, default="")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, default="")
    head = Column(String, default="")


class SchoolClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)  # e.g., "8", "9", "10"
    divisions = Column(JSON, nullable=False)  # ["A", "B", "C"]
    block = Column(String, default="")
    class_teacher = Column(String, default="")
    subjects = Column(JSON, nullable=False)  # [{name, periodsPerWeek, teacher}]


class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(JSON, nullable=False)  # Full timetable JSON
