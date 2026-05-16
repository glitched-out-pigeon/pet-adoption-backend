from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class ApplicationCreate(BaseModel):
    applicant_name: str
    applicant_email: str
    applicant_phone: Optional[str] = None
    animal_id: Optional[str] = None
    status: Optional[str] = "pending"
    reviewed_by: Optional[str] = None

class ApplicationUpdate(BaseModel):
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applicant_phone: Optional[str] = None
    animal_id: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[str] = None

@router.get("/")
async def get_applications():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT applications.*,
               animals.name as animal_name,
               employees.name as reviewer_name
        FROM applications
        LEFT JOIN animals ON applications.animal_id = animals.id
        LEFT JOIN employees ON applications.reviewed_by = employees.id
        ORDER BY applications.applied_at DESC
    """)
    await conn.close()
    return [dict(row) for row in rows]

@router.post("/")
async def add_application(data: ApplicationCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """INSERT INTO applications
           (applicant_name, applicant_email, applicant_phone, animal_id, status, reviewed_by)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
        data.applicant_name, data.applicant_email, data.applicant_phone,
        data.animal_id, data.status, data.reviewed_by
    )
    await conn.close()
    return dict(row)

@router.patch("/{application_id}")
async def update_application(application_id: str, data: ApplicationUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE applications SET
            applicant_name = COALESCE($1, applicant_name),
            applicant_email = COALESCE($2, applicant_email),
            applicant_phone = COALESCE($3, applicant_phone),
            animal_id = COALESCE($4, animal_id),
            status = COALESCE($5, status),
            reviewed_by = COALESCE($6, reviewed_by)
        WHERE id = $7 RETURNING *""",
        data.applicant_name, data.applicant_email, data.applicant_phone,
        data.animal_id, data.status, data.reviewed_by, application_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)

@router.delete("/{application_id}")
async def delete_application(application_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM applications WHERE id = $1", application_id)
    await conn.close()
    return {"message": "Application deleted"}