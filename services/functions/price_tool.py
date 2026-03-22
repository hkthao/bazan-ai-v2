"""
title: Giá cà phê Tây Nguyên
author: Bazan AI
description: Lấy giá cà phê nhân xô hiện tại từ giacaphe.com cho 5 tỉnh Tây Nguyên.
             Cập nhật tự động, hỗ trợ cache 30 phút.
version: 1.0.0
"""

import httpx
import time
import re
from datetime import datetime
from html.parser import HTMLParser
from pydantic import BaseModel, Field


# ── Constants & Mapping ──────────────────────────────────────────────────────

PROVINCES = {
    "đắk lắk": "Đắk Lắk",
    "dak lak": "Đắk Lắk",
    "daklak": "Đắk Lắk",
    "buôn ma thuột": "Đắk Lắk",
    "lâm đồng": "Lâm Đồng",
    "lam dong": "Lâm Đồng",
    "đà lạt": "Lâm Đồng",
    "da lat": "Lâm Đồng",
    "gia lai": "Gia Lai",
    "gialai": "Gia Lai",
    "pleiku": "Gia Lai",
    "kon tum": "Kon Tum",
    "kontum": "Kon Tum",
    "đắk nông": "Đắk Nông",
    "dak nong": "Đắk Nông",
    "gia nghĩa": "Đắk Nông",
    "tây nguyên": None,
    "tay nguyen": None,
    "tất cả": None,
    "tat ca": None,
}

TAY_NGUYEN_PROVINCES = ["Đắk Lắk", "Lâm Đồng", "Gia Lai", "Kon Tum", "Đắk Nông"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


# ── HTML Parser ───────────────────────────────────────────────────────────────

class PriceTableParser(HTMLParser):
    """Parser để extract mapping tỉnh -> class name từ HTML."""

    def __init__(self):
        super().__init__()
        self.province_classes: dict[str, str] = {}
        self._in_table = False
        self._in_row = False
        self._in_province_cell = False
        self._current_province = ""
        self._capture_next_span = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "tr":
            self._in_row = True
            self._current_province = ""
        if tag == "td" and self._in_row:
            self._in_province_cell = True
        if tag == "span" and self._in_row and self._capture_next_span:
            cls = attrs_dict.get("class", "")
            # Lấy class cuối cùng (thường là class chứa content price)
            if cls:
                class_parts = cls.split()
                if len(class_parts) > 1:
                    self.province_classes[self._current_province] = class_parts[-1]
                else:
                    self.province_classes[self._current_province] = cls
            self._capture_next_span = False
            self._current_province = ""  # Reset để tránh bắt span ở td tiếp theo

    def handle_endtag(self, tag):
        if tag == "td":
            self._in_province_cell = False
            # Nếu vừa đọc xong 1 province, chuẩn bị bắt span ở td tiếp theo
            if self._current_province in TAY_NGUYEN_PROVINCES:
                self._capture_next_span = True
        if tag == "tr":
            self._in_row = False
            self._capture_next_span = False

    def handle_data(self, data):
        if self._in_province_cell:
            text = data.strip()
            if text in TAY_NGUYEN_PROVINCES:
                self._current_province = text


# ── Scraper Logic ─────────────────────────────────────────────────────────────

_cache: dict = {"data": None, "timestamp": 0}
CACHE_TTL = 1800  # 30 phút


def _fetch_prices() -> list[dict] | None:
    """Crawl giacaphe.com và giải mã giá từ CSS."""
    now = time.time()
    if _cache["data"] and now - _cache["timestamp"] < CACHE_TTL:
        return _cache["data"]

    url = "https://giacaphe.com"
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            return None

        html = resp.text

        # 1. Trích xuất CSS mapping: .className::after { content:'price'; }
        # Regex tìm các quy tắc class::after có chứa content
        css_pattern = r"\.([a-zA-Z0-9_-]+)::after\s*{\s*content\s*:\s*'([^']*)'\s*;\s*}"
        css_mapping = dict(re.findall(css_pattern, html))

        # 2. Parse HTML để biết tỉnh nào dùng class nào
        parser = PriceTableParser()
        parser.feed(html)

        # 3. Kết hợp lại thành list giá
        results = []
        for province, class_name in parser.province_classes.items():
            price_str = css_mapping.get(class_name)
            if price_str:
                # Clean price_str: "94,000" -> 94000
                try:
                    price_int = int(price_str.replace(",", "").replace(".", ""))
                    results.append({
                        "province": province,
                        "price": price_int,
                        "price_str": price_str + " đ/kg"
                    })
                except ValueError:
                    continue

        if results:
            _cache["data"] = results
            _cache["timestamp"] = now
            return results

    except Exception:
        pass

    return None


# ── Tool class ────────────────────────────────────────────────────────────────

class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def get_coffee_price(self, province: str = "tất cả") -> str:
        """
        Lấy giá cà phê nhân xô hôm nay tại Tây Nguyên từ giacaphe.com.
        Hỗ trợ: Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông, hoặc 'tất cả'.
        :param province: Tên tỉnh hoặc 'tất cả'
        :return: Bảng giá cà phê và nhận xét thị trường
        """
        key = province.lower().strip()
        filter_province = PROVINCES.get(key, "NOT_FOUND")

        if filter_province == "NOT_FOUND":
            return (
                f"Không tìm thấy dữ liệu cho '{province}'. "
                "Hỗ trợ: Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông, hoặc 'tất cả'."
            )

        prices = _fetch_prices()

        if prices is None:
            return (
                "⚠️ Không thể lấy giá cà phê tự động từ giacaphe.com lúc này.\n"
                "Bạn có thể xem trực tiếp tại: https://giacaphe.com\n"
                "Hoặc hỏi đại lý thu mua tại địa phương."
            )

        # Lọc dữ liệu
        if filter_province:
            filtered = [p for p in prices if p["province"] == filter_province]
        else:
            filtered = prices

        if not filtered:
            return (
                f"Hiện tại chưa có dữ liệu giá mới nhất cho {province}.\n"
                "Xem trực tiếp: https://giacaphe.com"
            )

        # Format kết quả
        update_time = datetime.fromtimestamp(_cache["timestamp"]).strftime("%H:%M %d/%m/%Y")
        
        if filter_province:
            p = filtered[0]
            msg = (
                f"☕ **Giá cà phê tại {p['province']}**\n"
                f"🕒 Cập nhật: {update_time}\n"
                f"💰 Giá: **{p['price_str']}**\n\n"
            )
            # Nhận xét nhanh dựa trên mức giá
            if p["price"] >= 100000:
                msg += "📈 **Nhận xét:** Giá đang ở mức rất cao kỷ lục. Nếu đã đạt lợi nhuận kỳ vọng, bà con có thể cân nhắc chốt bán một phần."
            elif p["price"] >= 80000:
                msg += "📊 **Nhận xét:** Giá ở mức tốt. Bà con nên theo dõi sát diễn biến sàn London và New York để quyết định."
            else:
                msg += "📉 **Nhận xét:** Giá đang ở mức trung bình. Nếu không gấp, bà con có thể chờ đợi nhịp hồi phục của thị trường."
        else:
            lines = [
                "☕ **Bảng giá cà phê nhân xô Tây Nguyên**",
                f"🕒 Cập nhật: {update_time}\n",
                "| Tỉnh thành | Giá hôm nay |",
                "| :--- | :--- |"
            ]
            # Sắp xếp theo giá giảm dần
            sorted_prices = sorted(filtered, key=lambda x: x["price"], reverse=True)
            for p in sorted_prices:
                lines.append(f"| {p['province']:<10} | **{p['price_str']}** |")
            
            lines.append("\n*Nguồn: giacaphe.com*")
            msg = "\n".join(lines)

        return msg
