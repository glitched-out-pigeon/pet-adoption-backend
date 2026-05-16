from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class EmployeeCreate(BaseModel):
    name: str
    role: str
    email: str
    phone: Optional[str] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@router.get("/")
async def get_employees():
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM employees ORDER BY hired_at DESC")
    await conn.close()
    return [dict(row) for row in rows]

@router.post("/")
async def add_employee(data: EmployeeCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        "INSERT INTO employees (name, role, email, phone) VALUES ($1, $2, $3, $4) RETURNING *",
        data.name, data.role, data.email, data.phone
    )
    await conn.close()
    return dict(row)

@router.patch("/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE employees SET
            name = COALESCE($1, name),
            role = COALESCE($2, role),
            email = COALESCE($3, email),
            phone = COALESCE($4, phone)
        WHERE id = $5 RETURNING *""",
        data.name, data.role, data.email, data.phone, employee_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)

@router.delete("/{employee_id}")
async def delete_employee(employee_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM employees WHERE id = $1", employee_id)
    await conn.close()
    return {"message": "Employee deleted"}