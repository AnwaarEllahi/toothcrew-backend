# services_seed.py
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

services = [
    {"name":"Metal Braces","price":"₨ 250,000","type":"Ortho"},
    {"name":"Ceramic Braces","price":"₨ 300,000","type":"Ortho"},
    {"name":"Damon Braces","price":"₨ 300,000","type":"Ortho"},
    {"name":"Clear Aligners","price":"₨ 300,000","type":"Ortho"},
    {"name":"Retainers","price":"₨ 25,000 (Each)","type":"Ortho"},
    {"name":"Root Canal, Pre-Molar","price":"₨ 15,000","type":"Endo"},
    {"name":"Root Canal, Molar","price":"₨ 25,000","type":"Endo"},
    {"name":"ReRCT (Pre-Molar)","price":"₨ 20,000","type":"Endo"},
    {"name":"ReRCT (Molar)","price":"₨ 30,000","type":"Endo"},
    {"name":"Crown (PFM)","price":"₨ 15,000","type":"Prostho"},
    {"name":"Crown (Zirconia)","price":"₨ 35,000","type":"Prostho"},
    {"name":"Crown (eMax)","price":"₨ 55,000","type":"Prostho"},
    {"name":"Veneers Zirconia","price":"₨ 45,000","type":"Prostho"},
    {"name":"Veneers eMax","price":"₨ 55,000","type":"Prostho"},
    {"name":"Partial Denture","price":"₨ 50,000","type":"Prostho"},
    {"name":"Denture (Upper & Lower Arch)","price":"₨ 100,000","type":"Prostho"},
    {"name":"Implant Turkey","price":"₨ 100,000","type":"Prostho"},
    {"name":"Implant Swiss (SGS)","price":"₨ 150,000","type":"Prostho"},
    {"name":"Implant US (Bio Horizons)","price":"₨ 250,000","type":"Prostho"},
    {"name":"Implant Swiss (Straumann)","price":"₨ 400,000","type":"Prostho"},
    {"name":"Surgical Extraction","price":"₨ 25,000","type":"Maxillofacial"},
    {"name":"Wisdom Tooth Extraction","price":"₨ 10,000","type":"Maxillofacial"},
    {"name":"Flap Surgery per Quadrant","price":"₨ 50,000","type":"Maxillofacial"},
    {"name":"Root Debridement per Quadrant","price":"₨ 30,000","type":"Maxillofacial"},
    {"name":"GTR per Tooth (excl. bone & membrane)","price":"₨ 35,000","type":"Maxillofacial"},
    {"name":"Gingivectomy per Quadrant","price":"₨ 35,000","type":"Maxillofacial"},
    {"name":"Gingivoplasty per Quadrant","price":"₨ 30,000","type":"Maxillofacial"},
    {"name":"Crown Lengthening Surgery (per tooth)","price":"₨ 25,000","type":"Maxillofacial"},
    {"name":"Free Gingival Graft per Tooth","price":"₨ 50,000","type":"Maxillofacial"},
    {"name":"Connective Tissue Graft per Tooth","price":"₨ 50,000","type":"Maxillofacial"},
    {"name":"Paddicle Graft per Tooth","price":"₨ 20,000","type":"Maxillofacial"},
    {"name":"Any Other Minor Surgical Procedure","price":"₨ 25,000","type":"Maxillofacial"},
]

def seed():
    db = SessionLocal()
    try:
        for s in services:
            exists = db.query(models.Service).filter(models.Service.name == s["name"]).first()
            if not exists:
                service = models.Service(name=s["name"], price=s["price"], type=s["type"])
                db.add(service)
        db.commit()
        print("Seeding done.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
