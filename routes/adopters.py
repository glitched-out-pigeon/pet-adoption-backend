from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class AdopterCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    animal_id: Optional[str] = None
    processed_by: Optional[str] = None

class AdopterUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    animal_id: Optional[str] = None
    processed_by: Optional[str] = None

@router.get("/")
async def get_adopters():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT adopters.*,
               animals.name as animal_name,
               employees.name as employee_name
        FROM adopters
        LEFT JOIN animals ON adopters.animal_id = animals.id
        LEFT JOIN employees ON adopters.processed_by = employees.id
        ORDER BY adopters.adopted_at DESC
    """)
    await conn.close()
    return [dict(row) for row in rows]

@router.post("/")
async def add_adopter(data: AdopterCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        "INSERT INTO adopters (name, email, phone, animal_id, processed_by) VALUES ($1, $2, $3, $4, $5) RETURNING *",
        data.name, data.email, data.phone, data.animal_id, data.processed_by
    )
    await conn.close()
    return dict(row)

@router.patch("/{adopter_id}")
async def update_adopter(adopter_id: str, data: AdopterUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE adopters SET
            name = COALESCE($1, name),
            email = COALESCE($2, email),
            phone = COALESCE($3, phone),
            animal_id = COALESCE($4, animal_id),
            processed_by = COALESCE($5, processed_by)
        WHERE id = $6 RETURNING *""",
        data.name, data.email, data.phone,
        data.animal_id, data.processed_by, adopter_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Adopter not found")
    return dict(row)

@router.delete("/{adopter_id}")
async def delete_adopter(adopter_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM adopters WHERE id = $1", adopter_id)
    await conn.close()
    return {"message": "Adopter deleted"}