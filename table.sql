DROP TABLE drinks;
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector (벡터 검색용) [cite: 11]
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- pg_trgm (오타 교정 및 유사 검색용) [cite: 41]

CREATE TABLE IF NOT EXISTS drinks (
                    id SERIAL PRIMARY KEY,
                    drink_name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    caffeine_amount NUMERIC,
                    ice_type TEXT,
                    embedding VECTOR(1536), 
                    UNIQUE(drink_name, brand)
                );
CREATE INDEX IF NOT EXISTS idx_drinks_drink_name ON drinks(drink_name);
CREATE INDEX IF NOT EXISTS idx_drinks_brand ON drinks(brand);
CREATE INDEX IF NOT EXISTS idx_drinks_drink_name_trgm ON drinks USING gin (drink_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_drinks_embedding ON drinks USING hnsw (embedding vector_cosine_ops);
            