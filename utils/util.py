import pandas as pd
from pathlib import Path

def get_csv_path(file_name: str = "drinks.csv") -> Path:
    """스크립트 위치 기준 CSV 파일의 절대 경로를 반환합니다."""
    return Path(__file__).parent / file_name

def load_csv_data(file_path: Path) -> pd.DataFrame:
    """CSV를 로드하고 'id' 컬럼을 제거하여 반환합니다."""
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    df = pd.read_csv(file_path)
    return df