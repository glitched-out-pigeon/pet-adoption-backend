from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection
import bcrypt

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    conn = await get_connection()
    row = await conn.fetchrow(
        "SELECT * FROM admin_users WHERE email = $1", data.email
    )
    await conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_matches = bcrypt.checkpw(
        data.password.encode(),
        row["password_hash"].encode()
    )

    if not password_matches:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "success": True,
        "name": row["name"],
        "email": row["email"]
    }