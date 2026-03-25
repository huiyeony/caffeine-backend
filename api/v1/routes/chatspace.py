from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

from core.auth import get_current_user
from core.database import get_pool

router = APIRouter(prefix="/chatspaces")


@router.get("")
async def get_chatspaces(user_id: str = Depends(get_current_user)):
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT chatspace_id, title, created_at FROM chatspace "
                "WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return await cur.fetchall()


@router.post("")
async def create_chatspace(user_id: str = Depends(get_current_user)):
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO chatspace (user_id) VALUES (%s) RETURNING chatspace_id, created_at",
                (user_id,),
            )
            return await cur.fetchone()


@router.delete("/{chatspace_id}")
async def delete_chatspace(chatspace_id: str, user_id: str = Depends(get_current_user)):
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM chatspace WHERE chatspace_id = %s AND user_id = %s",
                (chatspace_id, user_id),
            )
    return {"message": "삭제 완료"}
