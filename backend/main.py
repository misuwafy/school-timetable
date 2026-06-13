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

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KKHMS Alathiyur - Timetable")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Schemas =====
class TeacherSchema(BaseModel):
    name: Optional[str] = None
    maxPeriodsPerDay: Optional[int] = 7
    isBlockHead: Optional[bool] = False
    headOfBlock: Optional[str] = ""


class BlockSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = ""
    head: Optional[str] = ""


class ClassSchema(BaseModel):
    name: Optional[str] = None
    divisions: Optional[list] = None
    block: Optional[str] = ""
    classTeacher: Optional[str] = ""
    subjects: Optional[list] = None


# ===== Teachers =====
@app.get("/api/teachers")
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).order_by(Teacher.name).all()
    return [{"id": t.id, "name": t.name, "maxPeriodsPerDay": t.maxPeriodsPerDay,
             "isBlockHead": t.isBlockHead, "headOfBlock": t.headOfBlock} for t in teachers]


@app.post("/api/teachers")
def create_teacher(data: TeacherSchema, db: Session = Depends(get_db)):
    t = Teacher(name=data.name, maxPeriodsPerDay=data.maxPeriodsPerDay,
                isBlockHead=data.isBlockHead, headOfBlock=data.headOfBlock)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name}


@app.put("/api/teachers/{tid}")
def update_teacher(tid: int, data: TeacherSchema, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == tid).first()
    if not t:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    return {"ok": True}


@app.delete("/api/teachers/{tid}")
def delete_teacher(tid: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == tid).first()
    if t:
        db.delete(t)
        db.commit()
    return {"ok": True}


# ===== Blocks =====
@app.get("/api/blocks")
def get_blocks(db: Session = Depends(get_db)):
    blocks = db.query(Block).all()
    return [{"id": b.id, "name": b.name, "description": b.description, "head": b.head} for b in blocks]


@app.post("/api/blocks")
def create_block(data: BlockSchema, db: Session = Depends(get_db)):
    b = Block(name=data.name, description=data.description, head=data.head)
    db.add(b)
    db.commit()
    db.refresh(b)
    return {"id": b.id, "name": b.name}


@app.put("/api/blocks/{bid}")
def update_block(bid: int, data: BlockSchema, db: Session = Depends(get_db)):
    b = db.query(Block).filter(Block.id == bid).first()
    if not b:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    return {"ok": True}


@app.delete("/api/blocks/{bid}")
def delete_block(bid: int, db: Session = Depends(get_db)):
    b = db.query(Block).filter(Block.id == bid).first()
    if b:
        db.delete(b)
        db.commit()
    return {"ok": True}


# ===== Classes =====
@app.get("/api/classes")
def get_classes(db: Session = Depends(get_db)):
    classes = db.query(SchoolClass).all()
    return [{"id": c.id, "name": c.name, "divisions": c.divisions, "block": c.block,
             "classTeacher": c.classTeacher, "subjects": c.subjects} for c in classes]


@app.post("/api/classes")
def create_class(data: ClassSchema, db: Session = Depends(get_db)):
    c = SchoolClass(name=data.name, divisions=data.divisions, block=data.block,
                    classTeacher=data.classTeacher, subjects=data.subjects)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@app.put("/api/classes/{cid}")
def update_class(cid: int, data: ClassSchema, db: Session = Depends(get_db)):
    c = db.query(SchoolClass).filter(SchoolClass.id == cid).first()
    if not c:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    return {"ok": True}


@app.delete("/api/classes/{cid}")
def delete_class(cid: int, db: Session = Depends(get_db)):
    c = db.query(SchoolClass).filter(SchoolClass.id == cid).first()
    if c:
        db.delete(c)
        db.commit()
    return {"ok": True}


# ===== Timetable =====
@app.get("/api/timetable")
def get_timetable(db: Session = Depends(get_db)):
    tt = db.query(Timetable).first()
    return tt.data if tt else {}


@app.post("/api/timetable")
def save_timetable(data: dict, db: Session = Depends(get_db)):
    db.query(Timetable).delete()
    db.add(Timetable(data=data))
    db.commit()
    return {"ok": True}


# ===== Serve Frontend =====
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/styles.css")
def serve_css():
    return FileResponse(os.path.join(frontend_path, "styles.css"))


@app.get("/app.js")
def serve_js():
    return FileResponse(os.path.join(frontend_path, "app.js"))
