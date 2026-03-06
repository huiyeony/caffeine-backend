# from typing import List
# from core.config import settings
# from rag.model import embeddings

# # Ollama 기반 임베딩 설정 로드
# # bge-m3 모델을 사용하여 고성능 시맨틱 벡터를 생성합니다.

# async def get_embeddings(texts: List[str]) -> List[List[float]]:
#     """여러 문서(텍스트)를 한 번에 벡터로 변환합니다."""
#     return await embeddings.aembed_documents(texts)

# async def get_query_embedding(query: str) -> List[float]:
#     """단일 검색 쿼리를 벡터로 변환합니다."""
#     return await embeddings.aembed_query(query)

from typing import List

from rag.model import embeddings

def get_query_embedding(query: str) -> list[float]:
    """질문 텍스트를 벡터로 변환합니다."""
    return embeddings.embed_query(query)
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """여러 문서(텍스트)를 한 번에 벡터로 변환합니다."""
    return await embeddings.aembed_documents(texts)

