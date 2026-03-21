"""Weather tool — 7-day forecast for Tay Nguyen coffee provinces."""

import httpx
from pydantic import BaseModel, Field


PROVINCES = {
    "dak_lak": {"name": "Đắk Lắk", "q": "Buon Ma Thuot,VN"},
    "lam_dong": {"name": "Lâm Đồng", "q": "Da Lat,VN"},
    "gia_lai": {"name": "Gia Lai", "q": "Pleiku,VN"},
    "kon_tum": {"name": "Kon Tum", "q": "Kon Tum,VN"},
    "dak_nong": {"name": "Đắk Nông", "q": "Gia Nghia,VN"},
}


class Tools:
    class Valves(BaseModel):
        OPENWEATHER_API_KEY: str = Field(default="", description="OpenWeatherMap API key")

    def __init__(self):
        self.valves = self.Valves()

    def get_weather(self, province: str) -> str:
        """
        Lấy dự báo thời tiết 7 ngày cho tỉnh Tây Nguyên.
        :param province: Tên tỉnh (dak_lak, lam_dong, gia_lai, kon_tum, dak_nong)
        :return: Thông tin thời tiết dạng text
        """
        info = PROVINCES.get(province.lower())
        if not info:
            return f"Không tìm thấy tỉnh '{province}'. Các tỉnh hỗ trợ: {', '.join(PROVINCES.keys())}"

        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={"q": info["q"], "appid": self.valves.OPENWEATHER_API_KEY,
                        "lang": "vi", "units": "metric", "cnt": 7},
                timeout=10.0,
            )
            data = resp.json()
            lines = [f"Thời tiết {info['name']}:"]
            for item in data.get("list", [])[:7]:
                lines.append(
                    f"- {item['dt_txt']}: {item['weather'][0]['description']}, "
                    f"{item['main']['temp']:.1f}°C, độ ẩm {item['main']['humidity']}%"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Lỗi khi lấy thời tiết: {e}"
