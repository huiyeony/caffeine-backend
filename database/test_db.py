import psycopg
from core.config import settings

def test_connection():
    try:
        with psycopg.connect(settings.database_url) as conn:
            print("성공: Postgres 데이터베이스에 연결되었습니다.")
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                print(f"DB 버전: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"실패: 연결 중 오류가 발생했습니다.\n{e}")

if __name__ == "__main__":
    test_connection()