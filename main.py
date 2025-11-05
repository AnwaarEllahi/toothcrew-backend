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



# create tables
Base.metadata.create_all(bind=engine)

# ✅ Create FastAPI app at the top
app = FastAPI(title="Clinic Backend (FastAPI)")


# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
#     doctor_id = payload.doctor_id

#    # If frontend sends doctor_name, find doctor_id automatically
#     if not doctor_id and payload.doctor_name:
#         doctor = db.query(models.User).filter(models.User.name == payload.doctor_name).first()
#         if doctor:
#             doctor_id = doctor.id
#         else:
#             raise HTTPException(status_code=404, detail=f"Doctor '{payload.doctor_name}' not found")
   


#     patient = models.Patient(
#         name=payload.name,
#         doctor_id=doctor_id,
#         contact=payload.contact,
#         date_of_birth=payload.date_of_birth,
#         medical_history=payload.medical_history,
#         city=payload.city,
#     )

#     db.add(patient)
#     db.commit()
#     db.refresh(patient)
#     return patient


@app.post("/patients", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
):
    # prefer explicit doctor_id, but allow resolving from doctor_name (doctors table)
    doctor_id = payload.doctor_id
    print("Received doctor_id:", doctor_id)
    # If frontend sent doctor_name (and not doctor_id), resolve it from the Doctor table
    doctor_name = getattr(payload, "doctor_name", None)
    if doctor_id is None and doctor_name:
        doctor = db.query(models.Doctor).filter(models.Doctor.name == doctor_name).first()
        if not doctor:
            raise HTTPException(status_code=404, detail=f"Doctor '{doctor_name}' not found")
        doctor_id = doctor.id

    # if a doctor_id was provided, validate it exists in doctors table
    if doctor_id is not None:
        exists = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
        if not exists:
            raise HTTPException(status_code=422, detail=f"doctor_id {doctor_id} does not exist")
    print(exists.__dict__)
    patient = models.Patient(
        name=payload.name,
        doctor_id=doctor_id,                    # FK or None (from doctors table)
        contact=payload.contact,
        date_of_birth=payload.date_of_birth,
        medical_history=payload.medical_history,
        city=payload.city,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return schemas.PatientOut.model_validate(patient, from_attributes=True).model_copy(
    update={"doctor_name": exists.name if exists else None}
    )




# @app.get("/patients", response_model=List[schemas.PatientOut])
# def list_patients(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#     print(current_user.id)
#     if (getattr(current_user, "role", "") or "").lower() == "doctor":
#         patients = db.query(models.Patient).filter(models.Patient.doctor_id == int(getattr(current_user, "id"))).all()
#     else:
#         patients = db.query(models.Patient).all()
#     return patients

# @app.get("/patients", response_model=List[schemas.PatientOut])
# def list_patients(db: Session = Depends(get_db)):
#     patients = db.query(models.Patient).all()
#     return patients




# @app.get("/patients", response_model=List[schemas.PatientOut])
# def list_patients(
#     db: Session = Depends(get_db),
#     month: int = Query(None, ge=1, le=12, description="Filter by month"),
#     year: int = Query(None, ge=1900, le=2100, description="Filter by year")
# ):
#     query = db.query(models.Patient)

#     if month and year:
#         query = query.filter(
#             func.extract('month', models.Patient.created_at) == month,
#             func.extract('year', models.Patient.created_at) == year
#         )
#     elif month:
#         query = query.filter(func.extract('month', models.Patient.created_at) == month)
#     elif year:
#         query = query.filter(func.extract('year', models.Patient.created_at) == year)

#     patients = query.all()

#     patients_with_doctor = []
#     for p in patients:
#         doctor_name = p.owner_doctor.name if p.owner_doctor else None
#         patient_dict = schemas.PatientOut.from_orm(p).dict()
#         patient_dict["doctor_name"] = doctor_name

#         # 🧩 Optionally hide doctor_id from frontend
#         if "doctor_id" in patient_dict:
#             del patient_dict["doctor_id"]

#         patients_with_doctor.append(patient_dict)

#     return patients_with_doctor


# @app.get("/patients", response_model=list[schemas.PatientOut])
# def list_patients(db: Session = Depends(get_db)):
#     patients = db.query(models.Patient).all()
#     today = date.today()
#     patient_list = []

#     for patient in patients:
#         dob_value = patient.date_of_birth   # coming from database
#         age = None

#         if dob_value is not None:
#             # Convert string to date if needed
#             if isinstance(dob_value, str):
#                 try:
#                     dob_date = datetime.strptime(dob_value, "%Y-%m-%d").date()
#                 except ValueError:
#                     # If the format is different, adjust "%Y-%m-%d" accordingly
#                     dob_date = None
#             else:
#                 dob_date = dob_value  # already a date object

#             if dob_date is not None:
#                 # Calculate age
#                 age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
#         if patient.owner_doctor is not None:
#             print("patient.owner_doctor", patient.owner_doctor.__dict__)            
#             print("owner_doctor", patient.__dict__)

#         patient_list.append({
#             "id": patient.id,
#             "name": patient.name,
#             "contact": patient.contact,
#             "date_of_birth": dob_date,
#             "age": age,
#             "medical_history": patient.medical_history,
#             "city": patient.city,
#             "doctor_id": patient.doctor_id,
#             "doctor_name": patient.owner_doctor if patient.owner_doctor else None,
#             "date": patient.created_at
#         })

#     return patient_list

# @app.get("/patients", response_model=list[schemas.PatientOut])
# def list_patients(db: Session = Depends(get_db)):
#     patients = db.query(models.Patient).all()
#     today = date.today()
#     patient_list = []

#     for patient in patients:
#         dob_value = patient.date_of_birth   # coming from database
#         age = None

#         if dob_value is not None:
#             # Convert string to date if needed
#             if isinstance(dob_value, str):
#                 try:
#                     dob_date = datetime.strptime(dob_value, "%Y-%m-%d").date()
#                 except ValueError:
#                     # If the format is different, adjust "%Y-%m-%d" accordingly
#                     dob_date = None
#             else:
#                 dob_date = dob_value  # already a date object

#             if dob_date is not None:
#                 # Calculate age
#                 age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

#         # ✅ FIX: Extract the doctor name properly
#         doctor_name = None
#         if patient.owner_doctor is not None:
#             doctor_name = patient.owner_doctor.name

#         patient_list.append({
#             "id": patient.id,
#             "name": patient.name,
#             "contact": patient.contact,
#             "date_of_birth": dob_date,
#             "age": age,
#             "medical_history": patient.medical_history,
#             "city": patient.city,
#             "doctor_id": patient.doctor_id,
#             "doctor_name": doctor_name,  # ✅ Now correctly returns just the name string
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

        doctor_name = None
        if patient.owner_doctor is not None:
            doctor_name = patient.owner_doctor.name

        patient_list.append({
            "id": patient.id,
            "name": patient.name,
            "contact": patient.contact,
            "date_of_birth": dob_date,
            "age": age,
            "medical_history": patient.medical_history,
            "city": patient.city,
            "doctor_id": patient.doctor_id,
            "doctor_name": doctor_name,
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
# @app.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
# def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db),
#                        current_user: models.User = Depends(require_role("admin", "receptionist"))):
#     appointment = models.Appointment(
#         patient_id=int(payload.patient_id),
#         doctor_id=int(payload.doctor_id),
#         appointment_datetime=payload.appointment_datetime,
#         status=payload.status,
#         notes=payload.notes
#     )
#     db.add(appointment)
#     db.commit()
#     db.refresh(appointment)
#     return appointment


# @app.post("/appointments", response_model=schemas.AppointmentOut)
# def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
#     appt = models.Appointment(
#         patient_name=payload.patient_name,                  # free text
#         doctor_id=payload.doctor_id,
#         appointment_datetime=payload.appointment_datetime,
#         status=payload.status,
#         notes=payload.notes,
#     )
#     db.add(appt)
#     db.commit()
#     db.refresh(appt)

#     # fetch the doctor INSTANCE, then use its .name (a str), not the Column
#     doctor = db.query(models.User).filter(models.User.id == appt.doctor_id).first()

#     # build response without mutating fields with Column types
#     out = schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
#         update={"doctor_name": doctor.name if doctor else None}
#     )
#     return out


    # out = schemas.AppointmentOut.from_orm(appointment)
    # out.patient_name = appointment.patient.name if appointment.patient else None
    # return out



# @app.get("/appointments", response_model=List[schemas.AppointmentOut])
# def list_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#     if (getattr(current_user, "role", "") or "").lower() == "doctor":
#         appts = db.query(models.Appointment).filter(models.Appointment.doctor_id == int(getattr(current_user, "id"))).all()
#     else:
#         appts = db.query(models.Appointment).all()
#     return appts

# @app.get("/appointments", response_model=List[schemas.AppointmentOut])
# def list_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#     if (getattr(current_user, "role", "") or "").lower() == "doctor":
#         appts = db.query(models.Appointment).filter(models.Appointment.doctor_id == int(getattr(current_user, "id"))).all()
#     else:
#         appts = db.query(models.Appointment).all()


#     result = []
#     for a in appts:
#     data = schemas.AppointmentOut.model_validate(a, from_attributes=True)
#     data.patient_name = a.patient.name if a.patient else None
#     result.append(data)
#     return result

    # attach patient_name to each
    # result = []
    # for a in appts:
    #     patient_name = a.patient.name if a.patient else None
    #     data = schemas.AppointmentOut.from_orm(a)
    #     data.patient_name = patient_name
    #     result.append(data)
    # return result



# @app.get("/appointments", response_model=List[schemas.AppointmentOut])
# def list_appointments(db: Session = Depends(get_db),
#                       current_user: models.User = Depends(get_current_user)):
#     if (getattr(current_user, "role", "") or "").lower() == "doctor":
#         appts = db.query(models.Appointment).filter(
#             models.Appointment.doctor_id == int(getattr(current_user, "id"))
#         ).all()
#     else:
#         appts = db.query(models.Appointment).all()

#     result = []
#     for a in appts:
#         data = schemas.AppointmentOut.model_validate(a, from_attributes=True)
#         data.patient_name = a.patient.name if a.patient else None
#         data.doctor_name = a.doctor.name if a.doctor else None
#         result.append(data)

#     return result


# @app.get("/appointments", response_model=list[schemas.AppointmentOut])
# def list_appointments(db: Session = Depends(get_db)):
#     appts = db.query(models.Appointment).all()
#     # prefetch doctor names
#     doctors = {u.id: u.name for u in db.query(models.User).all()}

#     result: list[schemas.AppointmentOut] = []
#     for a in appts:
#         result.append(
#             schemas.AppointmentOut.model_validate(a, from_attributes=True).model_copy(
#                 update={"doctor_name": doctors.get(a.doctor_id)}
#             )
#         )
#     return result

# ---------------- Appointments (fix create + list uses Doctor, not User) ----------------
from sqlalchemy.exc import IntegrityError
# -------------------- CREATE APPOINTMENT --------------------
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

    # If only patient_id is given, fetch the name from patients table
    if patient_id and not patient_name:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        patient_name = patient.name

    # ✅ Create appointment
    appt = models.Appointment(
        patient_id=patient_id,
        patient_name=patient_name,
        doctor_id=payload.doctor_id,
        appointment_datetime=payload.appointment_datetime,
        status=payload.status,
        notes=payload.notes,
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
    # print("Doctor:", doctor)
    # print("Appointment:", appt)
    # print("Doctor name to update:", doctor.name if doctor else None)
    return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
        update={"doctor_name": doctor.name if doctor else None}
    )
    # appt_out = schemas.AppointmentOut.model_validate(appt, from_attributes=True)
    # appt.doctor_name = doctor.name if doctor else None
    # print(appt)
    # return appt




# -------------------- LIST APPOINTMENTS --------------------
@app.get("/appointments", response_model=list[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    rows = (
        db.execute(
            select(
                models.Appointment,
                models.Doctor.name.label("doctor_name"),
            ).join(models.Doctor, models.Appointment.doctor_id == models.Doctor.id, isouter=True)
             .order_by(models.Appointment.appointment_datetime.asc())
        ).all()
    )

    out: List[schemas.AppointmentOut] = []
    for appt, doctor_name in rows:
        out.append(
            schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
                update={"doctor_name": doctor_name}
            )
        )
    return out
# -------------------- UPDATE APPOINTMENT --------------------
@app.put("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist"))
):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    data = payload.dict(exclude_unset=True)
    new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
    new_dt = data.get("appointment_datetime", appt.appointment_datetime)

    clash = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == new_doctor_id,
        models.Appointment.appointment_datetime == new_dt,
        models.Appointment.id != appointment_id,
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    for k, v in data.items():
        setattr(appt, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
    db.refresh(appt)

    doctor = db.query(models.Doctor).filter(models.Doctor.id == appt.doctor_id).first()
    return schemas.AppointmentOut.model_validate(appt, from_attributes=True).model_copy(
        update={"doctor_name": doctor.name if doctor else None}
    )




# -------------------- PARTIAL UPDATE --------------------
@app.patch("/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def partial_update_appointment(
    appointment_id: int,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))
):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    data = payload.dict(exclude_unset=True)
    new_doctor_id = int(data.get("doctor_id", appt.doctor_id))
    new_dt = data.get("appointment_datetime", appt.appointment_datetime)

    clash = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == new_doctor_id,
        models.Appointment.appointment_datetime == new_dt,
        models.Appointment.id != appointment_id,
    ).first()
    if clash:
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")

    for k, v in data.items():
        setattr(appt, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slot already booked for this doctor at that time.")
    db.refresh(appt)

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
# @app.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
# def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db),
#                   current_user: models.User = Depends(require_role("admin"))):
#     doctor = models.Doctor(name=payload.name, qualifications=payload.qualifications)
#     db.add(doctor)
#     db.commit()
#     db.refresh(doctor)
#     return doctor



# @app.put("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
# def update_doctor(
#     doctor_id: int,
#     payload: schemas.DoctorCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(require_role("admin"))
# ):
#     doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
#     if not doctor:
#         raise HTTPException(status_code=404, detail="Doctor not found")

#     # Update fields
#     doctor.name = payload.name  # type: ignore
#     doctor.qualifications = payload.qualifications  # type: ignore

#     db.commit()
#     db.refresh(doctor)
#     return doctor

# @app.get("/doctors", response_model=List[DoctorOut])
# def list_doctors(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
#     return db.query(models.Doctor).all()



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


# @app.get("/expenses", response_model=List[ExpenseOut])
# def list_expenses(db: Session = Depends(get_db),
#                   current_user: models.User = Depends(get_current_user)):
#     expenses = db.query(models.Expense).order_by(models.Expense.date.desc()).all()
#     return expenses

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

# @app.put("/expenses/{expense_id}", response_model=ExpenseOut)
# def update_expense(expense_id: int, payload: ExpenseCreate, db: Session = Depends(get_db)):
#     expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
#     if not expense:
#         raise HTTPException(status_code=404, detail="Expense not found")
#     for key, value in payload.dict().items():
#         setattr(expense, key, value)
#     db.commit()
#     db.refresh(expense)
#     return expense



# ---------------- Inventory ----------------


# @app.post("/inventory", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
# def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db),
#                      current_user: models.User = Depends(get_current_user)):
#     inventory = models.Inventory(
#         supplier=payload.supplier,
#         amount=payload.amount,
#         description=payload.description,
#         date=payload.date,
#         time=payload.time
#     )
#     db.add(inventory)
#     db.commit()
#     db.refresh(inventory)
#     return inventory


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
# @router.post("/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
# def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db),
#                     current_user: models.User = Depends(require_role("admin"))):
#     existing = db.query(models.Category).filter(func.lower(models.Category.name) == payload.name.lower()).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Category already exists")
#     c = models.Category(name=payload.name)
#     db.add(c)
#     db.commit()
#     db.refresh(c)
#     return c

# @router.get("/categories", response_model=List[schemas.CategoryOut])
# def list_categories(db: Session = Depends(get_db)):
#     return db.query(models.Category).order_by(models.Category.name).all()

# @router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_category(category_id: int, db: Session = Depends(get_db),
#                     current_user: models.User = Depends(require_role("admin"))):
#     cat = db.query(models.Category).filter(models.Category.id == category_id).first()
#     if not cat:
#         raise HTTPException(status_code=404, detail="Category not found")
#     db.delete(cat)
#     db.commit()
#     return


# # # --- Services ---
# @router.post("/services", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED)
# def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db),
#                    current_user: models.User = Depends(require_role("admin", "receptionist"))):
#     # ensure category exists
#     cat = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
#     if not cat:
#         raise HTTPException(status_code=404, detail="Category not found")
#     s = models.Service(
#         name=payload.name,
#         price_amount=payload.price_amount,
#         price_text=payload.price_text,
#         currency=payload.currency or "PKR",
#         category_id=payload.category_id,
#         is_active=True
#     )
#     db.add(s)
#     db.commit()
#     db.refresh(s)
#     return s

# @router.get("/services", response_model=List[schemas.ServiceOut])
# def list_services(db: Session = Depends(get_db),
#                   category_id: Optional[int] = Query(None, description="Filter by category id"),
#                   active: Optional[bool] = Query(None),
#                   q: Optional[str] = Query(None, description="search by name")):
#     query = db.query(models.Service)
#     if category_id:
#         query = query.filter(models.Service.category_id == category_id)
#     if active is not None:
#         query = query.filter(models.Service.is_active == active)
#     if q:
#         query = query.filter(models.Service.name.ilike(f"%{q}%"))
#     return query.order_by(models.Service.name).all()

# @router.put("/services/{service_id}", response_model=schemas.ServiceOut)
# def update_service(service_id: int, payload: schemas.ServiceUpdate, db: Session = Depends(get_db),
#                    current_user: models.User = Depends(require_role("admin", "receptionist"))):
#     s = db.query(models.Service).filter(models.Service.id == service_id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Service not found")
#     update_data = payload.dict(exclude_unset=True)
#     for k, v in update_data.items():
#         setattr(s, k, v)
#     db.commit()
#     db.refresh(s)
#     return s

# @router.patch("/services/{service_id}/toggle_active", response_model=schemas.ServiceOut)
# def toggle_service(service_id: int, db: Session = Depends(get_db),
#                    current_user: models.User = Depends(require_role("admin", "receptionist"))):
#     s = db.query(models.Service).filter(models.Service.id == service_id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Service not found")
#     s.is_active = not s.is_active
#     db.commit()
#     db.refresh(s)
#     return s

# @router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_service(service_id: int, db: Session = Depends(get_db),
#                    current_user: models.User = Depends(require_role("admin"))):
#     s = db.query(models.Service).filter(models.Service.id == service_id).first()
#     if not s:
#         raise HTTPException(status_code=404, detail="Service not found")
#     db.delete(s)
#     db.commit()
#     return



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

@app.get("/")
def read_root():
    return {"message": "Backend is working 🚀"}