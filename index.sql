-- 1. 필수 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector (벡터 검색용) [cite: 11]
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- pg_trgm (오타 교정 및 유사 검색용) [cite: 41]

-- 2. 벡터 검색 속도 향상을 위한 HNSW 인덱스 생성
-- 220만 건의 대규모 데이터셋 검색 속도를 최적화합니다. [cite: 21, 24]
CREATE INDEX ON drinks USING hnsw (embedding vector_cosine_ops);

-- 3. 오타 교정 및 유사 텍스트 검색을 위한 GIN trgm 인덱스 생성
-- Fuzzy Search를 구현하여 음료명 오타 발생 시에도 검색이 가능하게 합니다. [cite: 21, 41]
CREATE INDEX ON drinks USING gin (name gin_trgm_ops);

-- brand, name, ice_type 조합을 고유하게 만듭니다.
ALTER TABLE drinks 
ADD CONSTRAINT drinks_unique_combination UNIQUE (brand, name, ice_type);
-- 4. (선택) JSONB 메타데이터가 있다면 함수형 및 부분 인덱스 생성
-- 인덱스 저장 공간을 절약하고 검색 속도를 향상시킵니다. [cite: 21, 22]
-- CREATE INDEX idx_brand_partial ON drinks (brand_name) WHERE brand_name IS NOT NULL;
