# main.py
from xmlrpc.client import _datetime
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Dict, List
import models, schemas
from database import engine, Base, SessionLocal
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm

from schemas import DoctorCreate, DoctorOut, ExpenseCreate, ExpenseOut, InventoryCreate, InventoryOut
from datetime import datetime
from sqlalchemy import Tuple, extract, func, select
from fastapi import Query
from typing import cast
from typing import Optional
from sqlalchemy import func
from schemas import CompanyCreate, CompanyUpdate, CompanyOut
from sqlalchemy.exc import IntegrityError




# create tables
Base.metadata.create_all(bind=engine)

# ✅ Create FastAPI app at the top
app = FastAPI(title="Clinic Backend (FastAPI)")


# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=["https://pseudolobar-impetuously-wanda.ngrok-free.dev/ "],
    # # ngrok url and localhost for testing
    #  allow_origins=[
    #     "https://occur-tackle-snapshot-count.trycloudflare.com",  # ✅ Your Cloudflare URL
    #     "http://localhost:3000",
    # ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Auth ----------------
@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user_in.password)
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        role=user_in.role or "receptionist",
        password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # username field contains email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # use getattr to avoid static typing issues and pass Optional[str] to verify_password
    hashed = getattr(user, "password", None)
    if not verify_password(form_data.password, hashed):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(user_id=int(getattr(user, "id")), role=str(getattr(user, "role")))
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ---------------- Dashboard ----------------
@app.get("/dashboard")
def dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    first_of_month = today.replace(day=1)

    role = (getattr(current_user, "role", "") or "").lower()

    if role == "admin":
        total_patients_month = db.query(models.Patient).filter(models.Patient.created_at >= first_of_month).count()
        todays_appointments = db.query(models.Appointment).filter(
            models.Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
            models.Appointment.appointment_datetime <= datetime.combine(today, datetime.max.time())
        ).all()
        return {
            "role": "admin",
            "total_patients_this_month": total_patients_month,
            "todays_appointments_count": len(todays_appointments),
            "todays_appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "doctor_id": a.doctor_id,
                    "appointment_datetime": a.appointment_datetime,
                    "status": a.status,
                    "notes": a.notes
                } for a in todays_appointments
            ]
        }

    if role == "doctor":
        my_id = int(getattr(current_user, "id"))
        my_patients_count = db.query(models.Patient).filter(models.Patient.doctor_id == my_id).count()
        my_todays_appointments = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == my_id,
            models.Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
            models.Appointment.appointment_datetime <= datetime.combine(today, datetime.max.time())
        ).all()
        return {
            "role": "doctor",
            "my_patients_count": my_patients_count,
            "my_todays_appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "appointment_datetime": a.appointment_datetime,
                    "status": a.status,
                    "notes": a.notes
                } for a in my_todays_appointments
            ]
        }

    # receptionist / other roles
    total_patients_month = db.query(models.Patient).filter(models.Patient.created_at >= first_of_month).count()
    todays_appointments = db.query(models.Appointment).filter(
        models.Appointment.appointment_datetime >= datetime.combine(today, datetime.min.time()),
        models.Appointment.appointment_datetime <= datetime.combine(today, datetime.max.time())
    ).all()
    return {
        "role": role,
        "total_patients_this_month": total_patients_month,
        "todays_appointments_count": len(todays_appointments),
        "todays_appointments": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "appointment_datetime": a.appointment_datetime,
                "status": a.status,
                "notes": a.notes
            } for a in todays_appointments
        ]
    }





# ---------------- Patients ----------------




# @app.post("/patients", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
# def create_patient(
#     payload: schemas.PatientCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
# ):
#     # prefer explicit doctor_id, but allow resolving from doctor_name (doctors table)
#     doctor_id = payload.doctor_id
#     print("Received doctor_id:", doctor_id)
#     # If frontend sent doctor_name (and not doctor_id), resolve it from the Doctor table
#     doctor_name = getattr(payload, "doctor_name", None)
#     if doctor_id is None and doctor_name:
#         doctor = db.query(models.Doctor).filter(models.Doctor.name == doctor_name).first()
#         if not doctor:
#             raise HTTPException(status_code=404, detail=f"Doctor '{doctor_name}' not found")
#         doctor_id = doctor.id

#     # if a doctor_id was provided, validate it exists in doctors table
#     if doctor_id is not None:
#         exists = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
#         if not exists:
#             raise HTTPException(status_code=422, detail=f"doctor_id {doctor_id} does not exist")
#     print(exists.__dict__)
#     patient = models.Patient(
#         name=payload.name,
#         doctor_id=doctor_id,                    # FK or None (from doctors table)
#         contact=payload.contact,
#         date_of_birth=payload.date_of_birth,
#         medical_history=payload.medical_history,
#         city=payload.city,
        
#     )
#     db.add(patient)
#     db.commit()
#     db.refresh(patient)
#     return schemas.PatientOut.model_validate(patient, from_attributes=True).model_copy(
#     update={"doctor_name": exists.name if exists else None}
#     )

@app.post("/patients", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
):
    # resolve doctor_id from doctor_name if needed
    doctor_id = payload.doctor_id
    doctor_obj = None
    if doctor_id is None and payload.doctor_name:
        doctor_obj = db.query(models.Doctor).filter(models.Doctor.name == payload.doctor_name.strip()).first()
        if not doctor_obj:
            raise HTTPException(status_code=404, detail=f"Doctor '{payload.doctor_name}' not found")
        doctor_id = doctor_obj.id
    elif doctor_id is not None:
        doctor_obj = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
        if not doctor_obj:
            raise HTTPException(status_code=422, detail=f"doctor_id {doctor_id} does not exist")

    patient = models.Patient(
        name=payload.name.strip(),
        contact=payload.contact.strip(),             # string now
        date_of_birth=payload.date_of_birth,         # this is a date or None
        medical_history=payload.medical_history,
        city=payload.city,
        doctor_id=doctor_id,
        company_id=payload.company_id,               # save company
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return schemas.PatientOut.model_validate(patient, from_attributes=True).model_copy(
        update={
            "doctor_name": doctor_obj.name if doctor_obj else None,
            "company_name": patient.company.name if patient.company else None,
        }
    )

# @app.get("/patients", response_model=list[schemas.PatientOut])
# def list_patients(
#     month: int | None = Query(None),
#     year: int | None = Query(None),
#     db: Session = Depends(get_db)
# ):
#     query = db.query(models.Patient)

#     if month and year:
#         query = query.filter(
#             extract("month", models.Patient.created_at) == month,
#             extract("year", models.Patient.created_at) == year
#         )

#     patients = query.all()
#     today = date.today()
#     patient_list = []

#     for patient in patients:
#         dob_value = patient.date_of_birth
#         age = None

#         if dob_value is not None:
#             if isinstance(dob_value, str):
#                 try:
#                     dob_date = datetime.strptime(dob_value, "%Y-%m-%d").date()
#                 except ValueError:
#                     dob_date = None
#             else:
#                 dob_date = dob_value

#             if dob_date is not None:
#                 age = today.year - dob_date.year - (
#                     (today.month, today.day) < (dob_date.month, dob_date.day)
#                 )

#         # ✅ Safely get doctor name
#         doctor_name = None
#         if patient.owner_doctor is not None:
#             doctor_name = patient.owner_doctor.name
        
#         # ✅ Safely get company info with hasattr check
#         company_name = None
#         company_id = None
#         try:
#             if hasattr(patient, 'company') and patient.company is not None:
#                 company_name = patient.company.name
#                 company_id = patient.company_id
#             elif patient.company_id is not None:
#                 # If relationship not loaded but ID exists
#                 company_id = patient.company_id
#         except Exception as e:
#             print(f"Error accessing company for patient {patient.id}: {e}")
#             # Continue without company info

#         patient_list.append({
#             "id": patient.id,
#             "name": patient.name,
#             "contact": patient.contact,
#             "date_of_birth": dob_date if 'dob_date' in locals() else None,
#             "age": age,
#             "medical_history": patient.medical_history,
#             "city": patient.city,
#             "doctor_id": patient.doctor_id,
#             "doctor_name": doctor_name,
#             "company_id": company_id,
#             "company_name": company_name,
#             "created_at": patient.created_at
#         })

#     return patient_list

@app.get("/patients", response_model=list[schemas.PatientOut])
def list_patients(
    month: int | None = Query(None),
    year: int | None = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)

    if month and year:
        query = query.filter(
            extract("month", models.Patient.created_at) == month,
            extract("year", models.Patient.created_at) == year
        )

    patients = query.all()
    today = date.today()
    patient_list = []

    for patient in patients:
        dob_value = patient.date_of_birth
        age = None
        dob_date = None  # ✅ INITIALIZE HERE - outside the if block!

        if dob_value is not None:
            if isinstance(dob_value, str):
                try:
                    dob_date = datetime.strptime(dob_value, "%Y-%m-%d").date()
                except ValueError:
                    dob_date = None
            else:
                dob_date = dob_value

            if dob_date is not None:
                age = today.year - dob_date.year - (
                    (today.month, today.day) < (dob_date.month, dob_date.day)
                )

        # ✅ Safely get doctor name
        doctor_name = None
        if patient.owner_doctor is not None:
            doctor_name = patient.owner_doctor.name
        
        # ✅ Safely get company info with hasattr check
        company_name = None
        company_id = None
        try:
            if hasattr(patient, 'company') and patient.company is not None:
                company_name = patient.company.name
                company_id = patient.company_id
            elif patient.company_id is not None:
                # If relationship not loaded but ID exists
                company_id = patient.company_id
        except Exception as e:
            print(f"Error accessing company for patient {patient.id}: {e}")
            # Continue without company info

        patient_list.append({
            "id": patient.id,
            "name": patient.name,
            "contact": patient.contact,
            "date_of_birth": dob_date,  # ✅ FIXED - now uses the properly initialized variable
            "age": age,
            "medical_history": patient.medical_history,
            "city": patient.city,
            "doctor_id": patient.doctor_id,
            "doctor_name": doctor_name,
            "company_id": company_id,
            "company_name": company_name,
            "created_at": patient.created_at
        })

    return patient_list

@app.put("/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient(patient_id: int, payload: schemas.PatientUpdate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Update only provided fields
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return patient


# app = FastAPI()

@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}

# ---------------- Appointments ----------------

# ---------------- Appointments (fix create + list uses Doctor, not User) ----------------
from sqlalchemy.exc import IntegrityError
# -------------------- CREATE APPOINTMENT --------------------
# @app.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
# def create_appointment(
#     payload: schemas.AppointmentCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(require_role("admin", "receptionist"))
# ):
#     # ✅ Prevent double booking
#     clash = db.query(models.Appointment).filter(
#         models.Appointment.doctor_id == payload.doctor_id,
#         models.Appointment.appointment_datetime == payload.appointment_datetime
#     ).first()
#     if clash:
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

#     # ✅ Determine patient ID and name
#     patient_id = payload.patient_id
#     patient_name = payload.patient_name

#     # If only patient_id is given, fetch the name from patients table
#     if patient_id and not patient_name:
#         patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
#         patient_name = patient.name

#     # ✅ Create appointment
#     appt = models.Appointment(
#         patient_id=patient_id,
#         patient_name=patient_name,
#         doctor_id=payload.doctor_id,
#         appointment_datetime=payload.appointment_datetime,
#         status=payload.status,
#         notes=payload.notes,
#     )

#     db.add(appt)
    
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
#     db.refresh(appt)

#     # ✅ Fetch doctor name
#     doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
#     return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
#         update={"doctor_name": doctor.name if doctor else None}
#     )
   




# # -------------------- LIST APPOINTMENTS --------------------
# # -------------------- LIST APPOINTMENTS --------------------
# @app.get("/appointments", response_model=list[schemas.AppointmentOut])
# def list_appointments(db: Session = Depends(get_db),
#                       current_user: models.User = Depends(get_current_user)):
#     try:
#         rows = (
#             db.execute(
#                 select(
#                     models.Appointment,
#                     models.Doctor.name.label("doctor_name"),
#                     models.Company.name.label("company_name"),
#                 )
#                 .join(models.Doctor, models.Appointment.doctor_id == models.Doctor.id, isouter=True)
#                 .join(models.Company, models.Appointment.company_id == models.Company.id, isouter=True)
#                 .order_by(models.Appointment.appointment_datetime.asc())
#             ).all()
#         )

#         out: List[schemas.AppointmentOut] = []
#         for appt, doctor_name, company_name in rows:
#             # Convert the appointment object to dict first
#             appt_dict = {
#                 "id": appt.id,
#                 "doctor_id": appt.doctor_id,
#                 "company_id": appt.company_id,
#                 "patient_name": appt.patient_name,
#                 "appointment_datetime": appt.appointment_datetime,
#                 "status": appt.status,
#                 "notes": appt.notes,
#                 "doctor_name": doctor_name,
#                 "company_name": company_name,
#                 # Add any other fields from your Appointment model
#             }
#             out.append(schemas.AppointmentOut(**appt_dict))
        
#         return out
#     except Exception as e:
#         print(f"❌ Error in list_appointments: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

# # -------------------- UPDATE APPOINTMENT --------------------
# @app.put("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
# def update_appointment(
#     appointment_id: int,
#     payload: schemas.AppointmentUpdate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(require_role("admin", "receptionist"))
# ):
#     appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
#     if not appt:
#         raise HTTPException(status_code=404, detail="Appointment not found")

#     data = payload.dict(exclude_unset=True)
#     new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
#     new_dt = data.get("appointment_datetime", appt.appointment_datetime)

#     clash = db.query(models.Appointment).filter(
#         models.Appointment.doctor_id == new_doctor_id,
#         models.Appointment.appointment_datetime == new_dt,
#         models.Appointment.id != appointment_id,
#     ).first()
#     if clash:
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

#     for k, v in data.items():
#         setattr(appt, k, v)

#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
#     db.refresh(appt)

#     doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
#     return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
#         update={"doctor_name": doctor.name if doctor else None}
#     )




# # -------------------- PARTIAL UPDATE --------------------
# @app.patch("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
# def partial_update_appointment(
#     appointment_id: int,
#     payload: schemas.AppointmentUpdate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
# ):
#     appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
#     if not appt:
#         raise HTTPException(status_code=404, detail="Appointment not found")

#     data = payload.dict(exclude_unset=True)
#     new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
#     new_dt = data.get("appointment_datetime", appt.appointment_datetime)

#     clash = db.query(models.Appointment).filter(
#         models.Appointment.doctor_id == new_doctor_id,
#         models.Appointment.appointment_datetime == new_dt,
#         models.Appointment.id != appointment_id,
#     ).first()
#     if clash:
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

#     for k, v in data.items():
#         setattr(appt, k, v)

#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
#     db.refresh(appt)

#     doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
#     return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
#         update={"doctor_name": doctor.name if doctor else None}
#     )

#...................appointments...................
@app.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist"))
):
    # ✅ Prevent double booking
    clash = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == payload.doctor_id,
        models.Appointment.appointment_datetime == payload.appointment_datetime
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    # ✅ Determine patient ID and name
    patient_id = payload.patient_id
    patient_name = payload.patient_name
    patient_contact = payload.patient_contact  # <-- NEW

    # If only patient_id is given, fetch the name from patients table
    if patient_id and not patient_name:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient_name = patient.name
        # Optional (only if your Patient has a contact field):
        # if not patient_contact and getattr(patient, "contact", None):
        #     patient_contact = patient.contact

    # ✅ Create appointment
    appt = models.Appointment(
        patient_id=patient_id,
        patient_name=patient_name,
        patient_contact=patient_contact,                 # <-- NEW
        doctor_id=payload.doctor_id,
        appointment_datetime=payload.appointment_datetime,
        status=payload.status,
        notes=payload.notes,
        company_id=payload.company_id                    # <-- NEW (you were ignoring this)
    )

    db.add(appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
    db.refresh(appt)

    # ✅ Fetch doctor name
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
    return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
        update={"doctor_name": doctor.name if doctor else None}
    )

@app.get("/appointments", response_model=list[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    try:
        rows = (
            db.execute(
                select(
                    models.Appointment,
                    models.Doctor.name.label("doctor_name"),
                    models.Company.name.label("company_name"),
                )
                .join(models.Doctor, models.Appointment.doctor_id == models.Doctor.id, isouter=True)
                .join(models.Company, models.Appointment.company_id == models.Company.id, isouter=True)
                .order_by(models.Appointment.appointment_datetime.asc())
            ).all()
        )

        out: List[schemas.AppointmentOut] = []
        for appt, doctor_name, company_name in rows:
            appt_dict = {
                "id": appt.id,
                "doctor_id": appt.doctor_id,
                "company_id": appt.company_id,
                "patient_name": appt.patient_name,
                "patient_contact": appt.patient_contact,     # <-- NEW
                "appointment_datetime": appt.appointment_datetime,
                "status": appt.status,
                "notes": appt.notes,
                "doctor_name": doctor_name,
                "company_name": company_name,
            }
            out.append(schemas.AppointmentOut(**appt_dict))
        return out
    except Exception as e:
        print(f"❌ Error in list_appointments: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist"))
):
    # Fetch appointment
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Extract new values
    data = payload.dict(exclude_unset=True)
    new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
    new_dt = data.get("appointment_datetime", appt.appointment_datetime)

    # Prevent double-booking
    clash = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == new_doctor_id,
        models.Appointment.appointment_datetime == new_dt,
        models.Appointment.id != appointment_id,
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    # Update all fields dynamically (includes patient_contact)
    for key, value in data.items():
        setattr(appt, key, value)

    # Commit
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    db.refresh(appt)

    # Add doctor name to response
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
    return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
        update={"doctor_name": doctor.name if doctor else None}
    )


@app.patch("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def partial_update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
):
    # Fetch appointment
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Extract changed fields only
    data = payload.dict(exclude_unset=True)
    new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
    new_dt = data.get("appointment_datetime", appt.appointment_datetime)

    # Prevent doctor double-booking
    clash = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == new_doctor_id,
        models.Appointment.appointment_datetime == new_dt,
        models.Appointment.id != appointment_id,
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    # Apply only provided fields (includes patient_contact automatically)
    for key, value in data.items():
        setattr(appt, key, value)

    # Commit and refresh
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
    db.refresh(appt)

    # Include doctor name in response
    doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
    return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
        update={"doctor_name": doctor.name if doctor else None}
    )



# -------------------- TODAY’S APPOINTMENTS --------------------
@app.get("/appointments/today")
def todays_appointments(db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    appointments = db.query(models.Appointment).filter(
        models.Appointment.appointment_datetime >= start,
        models.Appointment.appointment_datetime <= end
    ).all()

    return {"todays_appointments": appointments}


# ---------------- Doctors ----------------



# Add this new endpoint for toggling doctor status
@app.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def toggle_doctor_status(
    doctor_id: int,
    payload: dict,  # Receives {"is_disabled": true/false}
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    if "is_disabled" in payload:
        doctor.is_disabled = payload["is_disabled"]
    
    db.commit()
    db.refresh(doctor)
    return doctor

# Your existing endpoints remain the same
@app.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    doctor = models.Doctor(
        name=payload.name,
        qualifications=payload.qualifications,
        pmdc_no=payload.pmdc_no,
        cnic=payload.cnic,
        is_disabled=payload.is_disabled or False,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor

@app.put("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: int,
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    doctor.name = payload.name
    doctor.qualifications = payload.qualifications
    doctor.pmdc_no = payload.pmdc_no
    doctor.cnic = payload.cnic
    doctor.is_disabled = payload.is_disabled or False
    
    db.commit()
    db.refresh(doctor)
    return doctor

@app.get("/doctors", response_model=List[DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Doctor).all()


@app.get("/doctors/{doctor_id}")
def get_doctor_by_id(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {
        "id": doctor.id,
        "name": doctor.name,
        "qualifications": doctor.qualifications
    }

# ---------------- Expenses ----------------


@app.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    expense = models.Expense(
        title=payload.title,
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        source=payload.source,  # ✅ Include this line

    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense



import datetime as dt  # ✅ one import, use dt.datetime everywhere

@app.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    source: Optional[str] = Query(None),
):
    q = db.query(models.Expense)

    if source:
        q = q.filter(models.Expense.source == source)

    if month and year:
        start = dt.datetime(year, month, 1)
        # next month
        next_month_year = year + (1 if month == 12 else 0)
        next_month = 1 if month == 12 else month + 1
        end = dt.datetime(next_month_year, next_month, 1)
        q = q.filter(models.Expense.date >= start, models.Expense.date < end)
    elif year:
        start = dt.datetime(year, 1, 1)
        end = dt.datetime(year + 1, 1, 1)
        q = q.filter(models.Expense.date >= start, models.Expense.date < end)

    return q.order_by(models.Expense.date.desc()).all()


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return




# ---------------- Inventory ----------------



@app.get("/inventory", response_model=List[InventoryOut])
def list_inventory(db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    items = db.query(models.Inventory).order_by(models.Inventory.id.desc()).all()
    return items


@app.delete("/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(inventory_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    record = db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    db.delete(record)
    db.commit()
    return

@app.post("/inventory", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory(payload: InventoryCreate,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):

    # Automatically get current date and time
    now = datetime.now()

    # If remaining_amount not sent, calculate it
    remaining = payload.amount - (payload.paid_amount or 0)

    inventory = models.Inventory(
        supplier=payload.supplier,
        invoice=payload.invoice,
        amount=payload.amount,
        paid_amount=payload.paid_amount or 0,        # store paid_amount
        remaining_amount=remaining if remaining >= 0 else 0,  # store remaining_amount
        description=payload.description,
        date=now.date().isoformat(),
        time=now.strftime("%H:%M:%S")
    )

    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory


# #.......services.........

# # --- Categories ---






 #.......services.........

# --- Categories ---
@app.post("/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_role("admin"))):
    existing = db.query(models.Category).filter(func.lower(models.Category.name) == payload.name.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    c = models.Category(name=payload.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@app.get("/categories", response_model=List[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()

@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_role("admin"))):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return


# # # --- Services ---
@app.post("/services", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin", "receptionist"))):
    # ensure category exists
    cat = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    s = models.Service(
        name=payload.name,
        price_amount=payload.price_amount,
        price_text=payload.price_text,
        currency=payload.currency or "PKR",
        category_id=payload.category_id,
        is_active=True
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.get("/services", response_model=List[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db),
                  category_id: Optional[int] = Query(None, description="Filter by category id"),
                  active: Optional[bool] = Query(None),
                  q: Optional[str] = Query(None, description="search by name")):
    query = db.query(models.Service)
    if category_id:
        query = query.filter(models.Service.category_id == category_id)
    if active is not None:
        query = query.filter(models.Service.is_active == active)
    if q:
        query = query.filter(models.Service.name.ilike(f"%{q}%"))
    return query.order_by(models.Service.name).all()

@app.put("/services/{service_id}", response_model=schemas.ServiceOut)
def update_service(service_id: int, payload: schemas.ServiceUpdate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin", "receptionist"))):
    s = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")
    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

@app.patch("/services/{service_id}/toggle_active", response_model=schemas.ServiceOut)
def toggle_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist"))
):
    s = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")
    s.is_active = not bool(s.is_active)
    db.commit()
    db.refresh(s)
    return s


@app.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin"))):
    s = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(s)
    db.commit()
    return




# ---------------- Invoices ----------------
@app.post("/invoices", response_model=schemas.InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    
    # Create invoice
    invoice = models.Invoice(
        invoice_no=payload.invoice_no,
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        patient_name=payload.patient_name,
        patient_age=payload.patient_age,
        patient_contact=payload.patient_contact,
        doctor_name=payload.doctor_name,
        date=payload.date,
        diagnosis=payload.diagnosis,
        subtotal=payload.subtotal,
        discount=payload.discount,  # Changed from invoice_discount
        total=payload.total  # Added total field
    )
    
    db.add(invoice)
    db.flush()  # Get the invoice ID
    
    # Create treatments
    for treatment_data in payload.treatments:
        treatment = models.InvoiceTreatment(
            invoice_id=invoice.id,
            description=treatment_data.description,  # Changed from procedure
            quantity=treatment_data.quantity,
            unit_price=treatment_data.unit_price,
            total=treatment_data.total
        )
        db.add(treatment)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@app.get("/invoices", response_model=List[schemas.InvoiceOut])
def list_invoices(db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user),
                  patient_id: int = Query(None, description="Filter by patient ID")):
    query = db.query(models.Invoice).order_by(models.Invoice.created_at.desc())
    
    if patient_id:
        query = query.filter(models.Invoice.patient_id == patient_id)
    
    invoices = query.all()
    return invoices


@app.get("/invoices/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@app.get("/invoices/number/{invoice_no}", response_model=schemas.InvoiceOut)
def get_invoice_by_number(invoice_no: str, db: Session = Depends(get_db),
                          current_user: models.User = Depends(get_current_user)):
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_no == invoice_no).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@app.patch("/invoices/{invoice_id}", response_model=schemas.InvoiceOut)
def update_invoice(invoice_id: int, payload: schemas.InvoiceUpdate, 
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update only provided fields
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(invoice, key, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@app.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin"))):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return


#................... company.............

# ---------------- Companies ----------------
@app.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    # unique (case-insensitive) name check
    existing = db.query(models.Company).filter(func.lower(models.Company.name) == payload.name.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")

    c = models.Company(
        name=payload.name.strip(),
        is_disabled=bool(payload.is_disabled) if payload.is_disabled is not None else False,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.get("/companies", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Company).order_by(models.Company.name.asc()).all()


@app.get("/companies/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    c = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    return c


@app.put("/companies/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    c = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")

    if payload.name and payload.name.strip().lower() != c.name.lower():
        clash = db.query(models.Company).filter(func.lower(models.Company.name) == payload.name.strip().lower()).first()
        if clash:
            raise HTTPException(status_code=400, detail="Company name already in use")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)

    db.commit()
    db.refresh(c)
    return c



@app.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    c = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(c)
    db.commit()
    return



@app.get("/")
def read_root():
    return {"message": "Backend is working 🚀"}