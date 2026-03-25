import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from psycopg.rows import dict_row

from core.auth import create_access_token, hash_password, verify_password
from core.database import get_pool

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(body: RegisterRequest):
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT user_id FROM users WHERE email = %s", (body.email,))
            if await cur.fetchone():
                raise HTTPException(400, "이미 가입된 이메일")
            await cur.execute(
                "INSERT INTO users (email, password, provider) VALUES (%s, %s, 'local')",
                (body.email, hash_password(body.password)),
            )
    return {"message": "회원가입 완료"}


@router.post("/guest/login")
async def guest_login():
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            guest_email = f"guest_{uuid.uuid4().hex}@guest.local"
            await cur.execute(
                "INSERT INTO users (email, provider) VALUES (%s, 'guest') RETURNING user_id",
                (guest_email,),
            )
            row = await cur.fetchone()
    return {"access_token": create_access_token(str(row["user_id"])), "token_type": "bearer"}


@router.post("/login")
async def login(body: LoginRequest):
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT user_id, password FROM users WHERE email = %s AND provider = 'local'",
                (body.email,),
            )
            user = await cur.fetchone()
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(401, "이메일 또는 비밀번호 오류")
    return {"access_token": create_access_token(str(user["user_id"])), "token_type": "bearer"}
