# main.py
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List
import models, schemas
from database import engine, Base, SessionLocal
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm

from schemas import DoctorCreate, DoctorOut, ExpenseCreate, ExpenseOut, InventoryCreate, InventoryOut
from datetime import datetime
from sqlalchemy import func
from fastapi import Query
from typing import cast




# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Backend (FastAPI)")

# CORS settings
origins = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow only your frontend origins
    allow_credentials=True,
    allow_methods=["*"],    # allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],    # allow any headers
)

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
@app.post("/patients", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: schemas.PatientCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_role("admin", "receptionist", "doctor"))):
    patient = models.Patient(
    name=payload.name,
    doctor_id=payload.doctor_id,
    contact=payload.contact,
    age=payload.age,
    medical_history=payload.medical_history,
    city=payload.city
)

    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

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





@app.get("/patients", response_model=List[schemas.PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    month: int = Query(None, ge=1, le=12, description="Filter by month"),
    year: int = Query(None, ge=1900, le=2100, description="Filter by year")
):
    query = db.query(models.Patient)

    if month and year:
        query = query.filter(
            func.extract('month', models.Patient.created_at) == month,
            func.extract('year', models.Patient.created_at) == year
        )
    elif month:
        query = query.filter(func.extract('month', models.Patient.created_at) == month)
    elif year:
        query = query.filter(func.extract('year', models.Patient.created_at) == year)

    patients = query.all()
    return patients



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




# ---------------- Appointments ----------------
@app.post("/appointments", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db),
                       current_user: models.User = Depends(require_role("admin", "receptionist"))):
    appointment = models.Appointment(
        patient_id=int(payload.patient_id),
        doctor_id=int(payload.doctor_id),
        appointment_datetime=payload.appointment_datetime,
        status=payload.status,
        notes=payload.notes
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@app.get("/appointments", response_model=List[schemas.AppointmentOut])
def list_appointments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if (getattr(current_user, "role", "") or "").lower() == "doctor":
        appts = db.query(models.Appointment).filter(models.Appointment.doctor_id == int(getattr(current_user, "id"))).all()
    else:
        appts = db.query(models.Appointment).all()
    return appts

@app.get("/appointments/today")
def todays_appointments(db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    # Get today's appointments
    appointments = db.query(models.Appointment).filter(
        models.Appointment.appointment_datetime >= start,
        models.Appointment.appointment_datetime <= end
    ).all()

    return {"todays_appointments": appointments}


# ---------------- Doctors ----------------
@app.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db),
                  current_user: models.User = Depends(require_role("admin"))):
    doctor = models.Doctor(name=payload.name, qualifications=payload.qualifications)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor



@app.put("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def update_doctor(
    doctor_id: int,
    payload: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Update fields
    doctor.name = payload.name  # type: ignore
    doctor.qualifications = payload.qualifications  # type: ignore

    db.commit()
    db.refresh(doctor)
    return doctor

@app.get("/doctors", response_model=List[DoctorOut])
def list_doctors(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Doctor).all()



# ---------------- Expenses ----------------


@app.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    expense = models.Expense(
        title=payload.title,
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/expenses", response_model=List[ExpenseOut])
def list_expenses(db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    expenses = db.query(models.Expense).order_by(models.Expense.date.desc()).all()
    return expenses


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
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    inventory = models.Inventory(
        supplier=payload.supplier,
        invoice=payload.invoice,  # ADD THIS LINE
        amount=payload.amount,
        description=payload.description,
        date=payload.date,
        time=payload.time
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

@app.get("/")
def read_root():
    return {"message": "Backend is working 🚀"}