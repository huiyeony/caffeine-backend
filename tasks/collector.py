import os
import requests
import psycopg
import asyncio
import time
from typing import List
from rag.model import embeddings # 기존 정의된 임베딩 로직

async def get_embeddings_sync(texts: List[str]) -> List[List[float]]:
    """Ollama 비동기 임베딩을 동기적으로 실행"""
    if not texts: return []
    return await embeddings.aembed_documents(texts)

async def sync_caffeine_data_pipeline():
    """1페이지부터 끝까지 전수 수집 파이프라인"""
    print(">>> [Task] Data Synchronization Pipeline Started...")
    
    url = "https://various.foodsafetykorea.go.kr/nutrient/general/nutr/listJson.do"
    page_num = 1
    page_size = 100

    try:
        from core.database import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                while True:
                    print(f"--- Processing Page {page_num} ---")
                    params = {
                        'pagenum': str(page_num),
                        'pagesize': str(page_size),
                        'searchText': '카페인',
                        'searchDetailMode': 'all'
                    }
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    data_list = response.json().get('returnMap', {}).get('dataList', [])

                    if not data_list:
                        print(">>> [Task] All pages processed.")
                        break

                    # 1. 임베딩 벡터 생성
                    food_names = [item.get('foodNmKr') for item in data_list]
                    print(f"    ㄴ Generating embeddings for {len(food_names)} items...")
                    vectors = await get_embeddings_sync(food_names)

                    # 2. DB UPSERT (중복 데이터 무시)
                    for item, vector in zip(data_list, vectors):
                        cur.execute("""
                            INSERT INTO caffeine_data 
                            (food_name, maker, caffeine_amount, serving_size, food_code, embedding)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (food_name, maker) DO NOTHING;
                        """, (
                            item.get('foodNmKr'), item.get('makerNm'),
                            item.get('searchNutri'), item.get('nutriServingSize'),
                            item.get('foodCd'), vector
                        ))
                    
                    conn.commit() # 페이지 단위 안정적 커밋
                    
                    if len(data_list) < page_size:
                        break
                    
                    page_num += 1
                    time.sleep(0.5) # API 부하 방지 매너 타임

    except Exception as e:
        print(f">>> [Task] Pipeline Error: {e}")