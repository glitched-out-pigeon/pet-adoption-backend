from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class VetRecordCreate(BaseModel):
    animal_id: str
    employee_id: str
    record_type: str
    notes: Optional[str] = None

class VetRecordUpdate(BaseModel):
    animal_id: Optional[str] = None
    employee_id: Optional[str] = None
    record_type: Optional[str] = None
    notes: Optional[str] = None

@router.get("/")
async def get_vet_records():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT vet_records.*,
               animals.name as animal_name,
               employees.name as employee_name
        FROM vet_records
        LEFT JOIN animals ON vet_records.animal_id = animals.id
        LEFT JOIN employees ON vet_records.employee_id = employees.id
        ORDER BY vet_records.recorded_at DESC
    """)
    await conn.close()
    return [dict(row) for row in rows]

@router.post("/")
async def add_vet_record(data: VetRecordCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        "INSERT INTO vet_records (animal_id, employee_id, record_type, notes) VALUES ($1, $2, $3, $4) RETURNING *",
        data.animal_id, data.employee_id, data.record_type, data.notes
    )
    await conn.close()
    return dict(row)

@router.patch("/{record_id}")
async def update_vet_record(record_id: str, data: VetRecordUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE vet_records SET
            animal_id = COALESCE($1, animal_id),
            employee_id = COALESCE($2, employee_id),
            record_type = COALESCE($3, record_type),
            notes = COALESCE($4, notes)
        WHERE id = $5 RETURNING *""",
        data.animal_id, data.employee_id,
        data.record_type, data.notes, record_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(row)

@router.delete("/{record_id}")
async def delete_vet_record(record_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM vet_records WHERE id = $1", record_id)
    await conn.close()
    return {"message": "Vet record deleted"}