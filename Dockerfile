FROM python:3.10-slim-bookworm

# 시스템 필수 패키지 및 빌드 도구 설치
# zlib1g-dev: zlib.h 헤더 파일을 제공하여 컴파일 에러를 해결합니다.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    python3-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# pip 업그레이드 및 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 전체 소스 코드 복사
COPY . .
# 실행 명령 (FastAPI 등)
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]