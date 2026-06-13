from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from database import engine, get_db, Base
from models import Teacher, Block, SchoolClass, Timetable

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KKHMS Alathiyur - Timetable Management")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic Schemas =====
class TeacherCreate(BaseModel):
    name: str
    max_periods_per_day: int = 7
    is_block_head: bool = False
    head_of_block: str = ""


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    max_periods_per_day: Optional[int] = None
    is_block_head: Optional[bool] = None
    head_of_block: Optional[str] = None


class BlockCreate(BaseModel):
    name: str
    description: str = ""
    head: str = ""


class BlockUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    head: Optional[str] = None


class ClassCreate(BaseModel):
    name: str
    divisions: list[str]
    block: str = ""
    class_teacher: str = ""
    subjects: list[dict]


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    divisions: Optional[list[str]] = None
    block: Optional[str] = None
    class_teacher: Optional[str] = None
    subjects: Optional[list[dict]] = None


class TimetableSave(BaseModel):
    data: dict


# ===== Teacher Endpoints =====
@app.get("/api/teachers")
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()


@app.post("/api/teachers")
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = Teacher(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


@app.put("/api/teachers/{teacher_id}")
def update_teacher(teacher_id: int, teacher: TeacherUpdate, db: Session = Depends(get_db)):
    db_teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    update_data = teacher.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_teacher, key, value)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


@app.delete("/api/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    db_teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db.delete(db_teacher)
    db.commit()
    return {"message": "Teacher deleted"}


# ===== Block Endpoints =====
@app.get("/api/blocks")
def get_blocks(db: Session = Depends(get_db)):
    return db.query(Block).all()


@app.post("/api/blocks")
def create_block(block: BlockCreate, db: Session = Depends(get_db)):
    db_block = Block(**block.model_dump())
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return db_block


@app.put("/api/blocks/{block_id}")
def update_block(block_id: int, block: BlockUpdate, db: Session = Depends(get_db)):
    db_block = db.query(Block).filter(Block.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")
    update_data = block.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_block, key, value)
    db.commit()
    db.refresh(db_block)
    return db_block


@app.delete("/api/blocks/{block_id}")
def delete_block(block_id: int, db: Session = Depends(get_db)):
    db_block = db.query(Block).filter(Block.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(db_block)
    db.commit()
    return {"message": "Block deleted"}


# ===== Class Endpoints =====
@app.get("/api/classes")
def get_classes(db: Session = Depends(get_db)):
    return db.query(SchoolClass).all()


@app.post("/api/classes")
def create_class(cls: ClassCreate, db: Session = Depends(get_db)):
    db_class = SchoolClass(**cls.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


@app.put("/api/classes/{class_id}")
def update_class(class_id: int, cls: ClassUpdate, db: Session = Depends(get_db)):
    db_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    update_data = cls.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_class, key, value)
    db.commit()
    db.refresh(db_class)
    return db_class


@app.delete("/api/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    db_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(db_class)
    db.commit()
    return {"message": "Class deleted"}


# ===== Timetable Endpoints =====
@app.get("/api/timetable")
def get_timetable(db: Session = Depends(get_db)):
    tt = db.query(Timetable).first()
    if tt:
        return tt.data
    return {}


@app.post("/api/timetable")
def save_timetable(tt: TimetableSave, db: Session = Depends(get_db)):
    # Delete existing and save new
    db.query(Timetable).delete()
    db_tt = Timetable(data=tt.data)
    db.add(db_tt)
    db.commit()
    return {"message": "Timetable saved"}


@app.delete("/api/timetable")
def delete_timetable(db: Session = Depends(get_db)):
    db.query(Timetable).delete()
    db.commit()
    return {"message": "Timetable deleted"}


# ===== Serve Frontend =====
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/styles.css")
def serve_css():
    return FileResponse(os.path.join(frontend_path, "styles.css"))


@app.get("/app.js")
def serve_js():
    return FileResponse(os.path.join(frontend_path, "app.js"))
