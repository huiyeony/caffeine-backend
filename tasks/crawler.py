import json
import re
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import boto3
import requests
from bs4 import BeautifulSoup

from core.config import settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 추상 베이스
# ══════════════════════════════════════════════════════════════
class BaseCrawler(ABC):
    brand_name: str
    total_pages: int = 1

    def crawl(self) -> list[dict]:
        results = []
        for page in range(1, self.total_pages + 1):
            logger.info(f"[{self.brand_name}] 페이지 {page}/{self.total_pages} 크롤링 중")
            items = self.crawl_page(page)
            results.extend(items)
            logger.info(f"  → {len(items)}개 수집 (누적 {len(results)}개)")
            time.sleep(0.5)
        return results

    @abstractmethod
    def crawl_page(self, page: int) -> list[dict]:
        ...

    @staticmethod
    def get(url: str, **kwargs) -> requests.Response:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15, **kwargs)
        return res

    @staticmethod
    def safe_float(val: str | None) -> float | None:
        try:
            return float(val.replace(",", "").strip()) if val else None
        except ValueError:
            return None

    @staticmethod
    def parse_volume_ml(text: str) -> int | None:
        m = re.search(r"(\d+)\s*ml", text, re.IGNORECASE)
        return int(m.group(1)) if m else None


# ══════════════════════════════════════════════════════════════
# 테라커피
# ══════════════════════════════════════════════════════════════
class TerraCoffeeCrawler(BaseCrawler):
    brand_name  = "teracoffee"
    total_pages = 6
    BASE_URL    = "https://teracoffee.com/default/drink/index.php"

    @staticmethod
    def _get_val(container, key: str) -> str | None:
        for font in container.find_all("font", style=lambda s: s and "12px" in s):
            text = font.get_text(strip=True)
            if key in text:
                return text.split(":")[-1].strip()
        return None

    def crawl_page(self, page: int) -> list[dict]:
        res = self.get(self.BASE_URL, params={"com_board_page": page})
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        items = []
        for title_tag in soup.select("span.gallery_title"):
            name = title_tag.get_text(strip=True)

            container = title_tag.parent
            while container:
                if container.find("font", style=lambda s: s and "12px" in s):
                    break
                container = container.parent

            if not container:
                continue

            volume_label = self._get_val(container, "용량")
            items.append({
                "brand":           self.brand_name,
                "name":            name,
                "category":        self._get_val(container, "카테고리"),
                "volume_label":    volume_label,
                "volume_ml":       self.parse_volume_ml(volume_label) if volume_label else None,
                "calories":        self.safe_float(self._get_val(container, "칼로리")),
                "carbs_g":         self.safe_float(self._get_val(container, "탄수화물")),
                "sugar_g":         self.safe_float(self._get_val(container, "당류")),
                "protein_g":       self.safe_float(self._get_val(container, "단백질")),
                "fat_g":           self.safe_float(self._get_val(container, "지방")),
                "saturated_fat_g": self.safe_float(self._get_val(container, "포화지방")),
                "sodium_mg":       self.safe_float(self._get_val(container, "나트륨")),
                "caffeine_mg":     self.safe_float(self._get_val(container, "카페인")),
                "allergens":       self._get_val(container, "알러지"),
                "crawled_at":      datetime.utcnow().isoformat(),
            })
        return items


# ══════════════════════════════════════════════════════════════
# 매머드커피
# ══════════════════════════════════════════════════════════════
class MammothCoffeeCrawler(BaseCrawler):
    brand_name  = "mammothcoffee"
    total_pages = 1  # 카테고리별 페이지네이션 없음
    LIST_URL    = "https://mmthcoffee.com/sub/menu/list_coffee_sub.php"
    DETAIL_URL  = "https://mmthcoffee.com/sub/menu/list_coffee_view.php"
    CATEGORIES  = ["C", "D", "N", "T", "B"]

    def crawl(self) -> list[dict]:
        results = []
        for cat in self.CATEGORIES:
            logger.info(f"[{self.brand_name}] 카테고리 {cat} 크롤링 중")
            items = self._crawl_category(cat)
            results.extend(items)
            logger.info(f"  → {len(items)}개 수집 (누적 {len(results)}개)")
        return results

    def crawl_page(self, page: int) -> list[dict]:
        # BaseCrawler 추상 메서드 충족용 — crawl() 오버라이드로 실제 사용 안 함
        return []

    def _crawl_category(self, menu_type: str) -> list[dict]:
        res = self.get(self.LIST_URL, params={"menuType": menu_type})
        ids = re.findall(r"goViewB\((\d+)\)", res.text)
        items = []
        for menu_seq in ids:
            records = self._crawl_detail(menu_seq)
            items.extend(records)
            time.sleep(0.3)
        return items

    def _crawl_detail(self, menu_seq: str) -> list[dict]:
        """HOT/ICE를 별도 레코드로 반환 (없으면 빈 리스트)."""
        res = self.get(self.DETAIL_URL, params={"menuSeq": menu_seq})
        soup = BeautifulSoup(res.text, "html.parser")

        # 음료명 — .i_tit 클래스
        name_tag = soup.select_one(".i_tit")
        if not name_tag:
            return []
        name = name_tag.get_text(strip=True)

        # 영양 정보 테이블: 첫 행이 헤더 ['구분', 'HOT(Xoz)', 'ICE(Xoz)']
        # 이후 행: ['칼로리 (Kcal)', hot_val, ice_val]
        tbl = soup.find("table")
        if not tbl:
            return []

        rows = tbl.find_all("tr")
        if not rows:
            return []

        # 헤더 파싱: HOT/ICE 열 인덱스 추출
        header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        hot_idx = next((i for i, h in enumerate(header_cells) if "HOT" in h.upper()), None)
        ice_idx = next((i for i, h in enumerate(header_cells) if "ICE" in h.upper()), None)

        # 영양소 맵 구성
        nutrient_map: dict[str, list[str | None]] = {}  # key → [hot_val, ice_val]
        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            if len(cells) < 2:
                continue
            key = cells[0]
            hot_val = cells[hot_idx] if hot_idx and hot_idx < len(cells) else None
            ice_val = cells[ice_idx] if ice_idx and ice_idx < len(cells) else None
            nutrient_map[key] = [hot_val, ice_val]

        def _pick_val(idx, *keys):
            for k in keys:
                for nk, vals in nutrient_map.items():
                    if k in nk:
                        return vals[idx]
            return None

        records = []
        for idx, ice_type in [(0, "HOT"), (1, "ICE")]:
            records.append({
                "brand":           self.brand_name,
                "name":            name,
                "ice_type":        ice_type,
                "calories":        self.safe_float(_pick_val(idx, "칼로리")),
                "carbs_g":         self.safe_float(_pick_val(idx, "탄수화물")),
                "sugar_g":         self.safe_float(_pick_val(idx, "당류")),
                "protein_g":       self.safe_float(_pick_val(idx, "단백질")),
                "fat_g":           self.safe_float(_pick_val(idx, "지방")),
                "saturated_fat_g": self.safe_float(_pick_val(idx, "포화지방")),
                "sodium_mg":       self.safe_float(_pick_val(idx, "나트륨")),
                "caffeine_mg":     self.safe_float(_pick_val(idx, "카페인")),
                "crawled_at":      datetime.utcnow().isoformat(),
            })
        return records


# ══════════════════════════════════════════════════════════════
# 브랜드 레지스트리 — 새 브랜드는 여기에만 추가
# ══════════════════════════════════════════════════════════════
BRAND_REGISTRY: dict[str, type[BaseCrawler]] = {
    "teracoffee":    TerraCoffeeCrawler,
    "mammothcoffee": MammothCoffeeCrawler,
}


# ══════════════════════════════════════════════════════════════
# S3 업로드
# ══════════════════════════════════════════════════════════════
def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def upload_raw_to_s3(brand: str, data: list[dict]) -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    s3_key = f"raw/{brand}/drinks_{date_str}.json"

    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    _get_s3_client().put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=body,
        ContentType="application/json",
    )
    logger.info(f">>> [Crawler] S3 업로드 완료: s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}")
    return s3_key


async def run_crawler(brand: str = "teracoffee") -> str:
    """크롤링 실행 → S3 raw 저장. 저장된 S3 key 반환."""
    crawler_cls = BRAND_REGISTRY.get(brand)
    if not crawler_cls:
        raise ValueError(f"등록되지 않은 브랜드: {brand}")

    logger.info(f">>> [Crawler] {brand} 크롤링 시작...")
    data = crawler_cls().crawl()
    logger.info(f">>> [Crawler] {len(data)}개 수집 완료")

    return upload_raw_to_s3(brand, data)
