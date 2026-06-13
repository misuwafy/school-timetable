"""Run this script once to seed teachers into the database."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine, SessionLocal, Base
from models import Teacher

Base.metadata.create_all(bind=engine)

teachers = [
    'Salma', 'Shyni Noor', 'Prajula', 'Nasheeda', 'Waheeda', 'Raheela', 'Muneera', 'Swathy', 'Santhosh', 'Fida',
    'Manju', 'Aslaha', 'Afla', 'Shahida', 'Shaniba', 'Shoukath', 'Abida', 'Naseeha', 'Dhanya', 'Naveen',
    'Afira', 'Shareena', 'Jitha', 'Sabu', 'Nusrath', 'Arifa KM', 'Saleena A', 'Nansar', 'Sakeena', 'Rasheed',
    'Sumitha', 'Shafeedha', 'Jamshy', 'Shafni', 'Zubair', 'Priya PA', 'T Banu', 'Sameera P', 'Asif', 'Fuaad',
    'SS New', 'Dineshan', 'Shanavas', 'Kamarudheen', 'Mirdas', 'JK', 'Jasheela', 'Swalih', 'Abdu Rahimaan', 'Shamseena',
    'Shamitha', 'Suneera', 'Priya P P', 'MK', 'Safiya', 'Nisha', 'Bejoy', 'Fousiya', 'Junaiha', 'Sameera T',
    'Sameera KK', 'Ashraf', 'Saleena', 'Harsha', 'Harifa', 'Bavakutty', 'Sughitha', 'Jaseena', 'Rafi', 'Manjula',
    'Ramseena', 'Jaleela', 'Romila', 'Mufsil', 'Saheer', 'Saeeda', 'Naseema', 'Zakaraiya', 'Mufeedha', 'Musthafa',
    'Yasir', 'Thesni', 'Jisha', 'Rekha', 'Sreeja', 'Muhsina', 'Eng (New)', 'Amina', 'Febin', 'Ayisha',
    'Jency', 'Rishad', 'Rameesha', 'Soniya', 'Shafeeque', 'Bineesh', 'Subaida', 'Rashid', 'Jijitha', 'Fathima',
    'Bindya', 'Ramsheeda', 'Rajani', 'Jasiya', 'Shyni', 'Risana', 'Satheesh', 'Deepthi', 'Pradeep', 'Thulasi',
    'Ranju', 'Abdulla', 'Sunil', 'Safeer', 'Sreeja M', 'Udayesh', 'Sheeba', 'Divya', 'Shajir'
]

db = SessionLocal()

# Only seed if no teachers exist
existing = db.query(Teacher).count()
if existing == 0:
    for name in teachers:
        db.add(Teacher(name=name.strip(), maxPeriodsPerDay=7, isBlockHead=False, headOfBlock=''))
    db.commit()
    print(f"✅ {len(teachers)} teachers seeded into database.")
else:
    print(f"ℹ️ Database already has {existing} teachers. Skipping seed.")

db.close()
