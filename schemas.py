# schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "receptionist"
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    role: str

class PatientCreate(BaseModel):
    name: str
    doctor_id: Optional[int] 
    contact : int
    age : int 
    medical_history : str
    city: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str]
    doctor_id: Optional[int]
    contact: Optional[int]
    age: Optional[int]
    medical_history: Optional[str]
    city: Optional[str]


class PatientOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    doctor_id: Optional[int]
    contact: int
    age: Optional[int] = None
    medical_history: Optional[str] = None
    city: Optional[str] = None

    class Config:
        orm_mode = True

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_datetime: datetime
    status: Optional[str] = "scheduled"
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_datetime: datetime
    status: str
    notes: Optional[str]

    class Config:
        orm_mode = True

# schemas.py

class DoctorCreate(BaseModel):
    name: str
    qualifications: str

class DoctorOut(BaseModel):
    id: int
    name: str
    qualifications: str

    class Config:
        orm_mode = True

# schemas.py (services)
from pydantic import BaseModel
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    price: str
    type: str
    description: Optional[str] = None

class ServiceOut(BaseModel):
    id: int
    name: str
    price: str
    type: str
    description: Optional[str] = None

    class Config:
        orm_mode = True


# ---------------- Expense Schemas ----------------
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ExpenseBase(BaseModel):
    title: str
    amount: int
    category: Optional[str] = None
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseOut(ExpenseBase):
    id: int
    date: datetime

    class Config:
        orm_mode = True

# --- inventory schemas ---
class InventoryCreate(BaseModel):
    supplier: str
    invoice: str
    amount: float
    description: str
    date: str
    time: str


class InventoryOut(BaseModel):
    id: int
    supplier: str
    invoice: str
    amount: float
    description: str
    date: str
    time: str
    created_at: datetime

    class Config:
        orm_mode = True


# #...... servies schemas ..........
# class CategoryBase(BaseModel):
#     name: str = Field(..., example="Ortho")

# class CategoryCreate(CategoryBase):
#     pass

# class CategoryOut(CategoryBase):
#     id: int
#     created_at: Optional[datetime]

#     class Config:
#         orm_mode = True

# class ServiceBase(BaseModel):
#     name: str = Field(..., example="Root Canal")
#     price_text: Optional[str] = Field(None, example="Rs. 2000")
#     price_amount: Optional[int] = Field(None, example=2000, description="Price in PKR integer")
#     currency: Optional[str] = Field("PKR")

# class ServiceCreate(ServiceBase):
#     category_id: int

# class ServiceUpdate(BaseModel):
#     name: Optional[str]
#     price_text: Optional[str]
#     price_amount: Optional[int]
#     is_active: Optional[bool]
#     category_id: Optional[int]

# class ServiceOut(ServiceBase):
#     id: int
#     category_id: int
#     is_active: bool
#     created_at: Optional[datetime]
#     updated_at: Optional[datetime]

#     class Config:
#         orm_mode = True
