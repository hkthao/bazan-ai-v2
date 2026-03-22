"""
title: Thời tiết Tây Nguyên
author: Bazan AI
description: Lấy thông tin thời tiết hiện tại và dự báo cho 5 tỉnh Tây Nguyên,
             kèm nhận xét về điều kiện canh tác cà phê.
version: 1.0.0
"""

import httpx
from datetime import datetime
from pydantic import BaseModel, Field


PROVINCES = {
    # Đắk Lắk
    "đắk lắk": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},
    "dak lak": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},
    "daklak": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},
    "đắk lắc": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},
    "buôn ma thuột": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},
    "buon ma thuot": {"q": "Buon Ma Thuot,VN", "name": "Đắk Lắk"},

    # Lâm Đồng
    "lâm đồng": {"q": "Da Lat,VN", "name": "Lâm Đồng"},
    "lam dong": {"q": "Da Lat,VN", "name": "Lâm Đồng"},
    "lamdong": {"q": "Da Lat,VN", "name": "Lâm Đồng"},
    "đà lạt": {"q": "Da Lat,VN", "name": "Lâm Đồng"},
    "da lat": {"q": "Da Lat,VN", "name": "Lâm Đồng"},

    # Gia Lai
    "gia lai": {"q": "Pleiku,VN", "name": "Gia Lai"},
    "gialai": {"q": "Pleiku,VN", "name": "Gia Lai"},
    "pleiku": {"q": "Pleiku,VN", "name": "Gia Lai"},
    "plei ku": {"q": "Pleiku,VN", "name": "Gia Lai"},

    # Kon Tum
    "kon tum": {"q": "Kon Tum,VN", "name": "Kon Tum"},
    "kontum": {"q": "Kon Tum,VN", "name": "Kon Tum"},

    # Đắk Nông
    "đắk nông": {"q": "Gia Nghia,VN", "name": "Đắk Nông"},
    "dak nong": {"q": "Gia Nghia,VN", "name": "Đắk Nông"},
    "daknong": {"q": "Gia Nghia,VN", "name": "Đắk Nông"},
    "gia nghĩa": {"q": "Gia Nghia,VN", "name": "Đắk Nông"},
    "gia nghia": {"q": "Gia Nghia,VN", "name": "Đắk Nông"},
}

WEATHER_VI = {
    "clear sky": "trời quang",
    "few clouds": "ít mây",
    "scattered clouds": "mây rải rác",
    "broken clouds": "nhiều mây",
    "overcast clouds": "trời âm u nhiều mây",
    "light rain": "mưa nhẹ",
    "moderate rain": "mưa vừa",
    "heavy intensity rain": "mưa to",
    "very heavy rain": "mưa rất to",
    "thunderstorm": "giông sấm sét",
    "thunderstorm with rain": "giông kèm mưa",
    "drizzle": "mưa phùn",
    "mist": "sương mù nhẹ",
    "fog": "sương mù dày",
    "haze": "sương mù khô",
    "smoke": "khói mù",
    "overcast": "trời âm u",
}


def _translate_weather(description: str) -> str:
    desc_lower = description.lower()
    return WEATHER_VI.get(desc_lower, description)


def _farming_advice(
    temp: float,
    humidity: float,
    rain_mm: float,
    wind_speed: float,
    description: str,
) -> str:
    advice = []

    # Tưới nước
    if rain_mm >= 25:
        advice.append("Không cần tưới — mưa đủ bù nhu cầu cây")
    elif rain_mm >= 10:
        advice.append("Có thể lùi lịch tưới 2–3 ngày")
    elif humidity < 50 and temp > 33:
        advice.append("Cần tưới sớm — trời nóng và khô, cây mất nước nhanh")
    elif temp > 35:
        advice.append("Tưới vào sáng sớm hoặc chiều tối, tránh tưới ban ngày")
    else:
        advice.append("Theo dõi độ ẩm đất để quyết định tưới")

    # Phun thuốc / bón phân
    if wind_speed > 20:
        advice.append("Không nên phun thuốc hoặc bón phân lá — gió mạnh")
    elif "rain" in description.lower() or "thunderstorm" in description.lower():
        advice.append("Không nên phun thuốc hoặc bón phân lá — trời mưa")
    else:
        advice.append("Điều kiện phù hợp để phun thuốc hoặc bón phân lá")

    # Cảnh báo đặc biệt
    if temp > 35:
        advice.append("⚠ Nhiệt độ cao — cây dễ bị stress nhiệt, kiểm tra độ ẩm đất")
    if humidity > 90 and "rain" not in description.lower():
        advice.append("⚠ Độ ẩm cao kéo dài — nguy cơ bệnh nấm, kiểm tra lá cây")

    return " | ".join(advice)


class Tools:
    class Valves(BaseModel):
        OPENWEATHER_API_KEY: str = Field(
            default="",
            description="API key từ openweathermap.org (miễn phí)",
        )

    def __init__(self):
        self.valves = self.Valves()

    def get_weather(self, province: str) -> str:
        """
        Lấy thông tin thời tiết hiện tại cho tỉnh Tây Nguyên.
        Hỗ trợ: Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông.
        :param province: Tên tỉnh (có dấu hoặc không dấu đều được)
        :return: Thông tin thời tiết và nhận xét canh tác
        """
        if not self.valves.OPENWEATHER_API_KEY:
            return (
                "Chưa cấu hình API key thời tiết. "
                "Vào Admin Panel → Tools → weather_tool → Valves → "
                "điền OPENWEATHER_API_KEY từ openweathermap.org (đăng ký miễn phí)."
            )

        # Normalize tên tỉnh
        key = province.lower().strip()
        info = PROVINCES.get(key)

        if not info:
            provinces_list = "Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông"
            return (
                f"Không tìm thấy tỉnh '{province}'. "
                f"Các tỉnh hỗ trợ: {provinces_list}."
            )

        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": info["q"],
                    "appid": self.valves.OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "vi",
                },
                timeout=10.0,
            )

            if resp.status_code == 401:
                return "API key không hợp lệ. Kiểm tra lại OPENWEATHER_API_KEY."
            if resp.status_code == 404:
                return f"Không tìm thấy dữ liệu thời tiết cho {info['name']}."

            resp.raise_for_status()
            data = resp.json()

            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"] * 3.6  # m/s → km/h
            rain_mm = data.get("rain", {}).get("1h", 0)
            clouds = data["clouds"]["all"]

            desc_vi = _translate_weather(description)
            advice = _farming_advice(temp, humidity, rain_mm, wind_speed, description)

            now = datetime.now().strftime("%H:%M %d/%m/%Y")

            result = f"""🌤 Thời tiết {info['name']} — {now}

Nhiệt độ: {temp:.1f}°C (cảm giác {feels_like:.1f}°C)
Thời tiết: {desc_vi}
Độ ẩm: {humidity}%
Gió: {wind_speed:.0f} km/h
Mây: {clouds}%"""

            if rain_mm > 0:
                result += f"\nMưa (1h qua): {rain_mm:.1f} mm"

            result += f"\n\n📋 Nhận xét canh tác:\n{advice}"

            return result

        except httpx.TimeoutException:
            return f"Không thể lấy thời tiết {info['name']} — kết nối timeout. Thử lại sau."
        except httpx.HTTPError as e:
            return f"Lỗi khi lấy thời tiết: {str(e)}"
        except Exception as e:
            return f"Lỗi không xác định: {str(e)}"

    def get_forecast(self, province: str) -> str:
        """
        Lấy dự báo thời tiết 5 ngày tới cho tỉnh Tây Nguyên.
        Hỗ trợ: Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông.
        :param province: Tên tỉnh (có dấu hoặc không dấu đều được)
        :return: Dự báo thời tiết 5 ngày và nhận xét canh tác
        """
        if not self.valves.OPENWEATHER_API_KEY:
            return "Chưa cấu hình OPENWEATHER_API_KEY."

        key = province.lower().strip()
        info = PROVINCES.get(key)

        if not info:
            return (
                f"Không tìm thấy tỉnh '{province}'. "
                "Hỗ trợ: Đắk Lắk, Lâm Đồng, Gia Lai, Kon Tum, Đắk Nông."
            )

        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={
                    "q": info["q"],
                    "appid": self.valves.OPENWEATHER_API_KEY,
                    "units": "metric",
                    "cnt": 5,  # 5 time slots x 3h = 15h tới
                    "lang": "vi",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            lines = [f"📅 Dự báo {info['name']} (15 giờ tới):"]
            total_rain = 0

            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"]).strftime("%H:%M %d/%m")
                temp = item["main"]["temp"]
                desc = _translate_weather(item["weather"][0]["description"])
                rain = item.get("rain", {}).get("3h", 0)
                total_rain += rain
                line = f"  {dt}: {temp:.0f}°C, {desc}"
                if rain > 0:
                    line += f", mưa {rain:.1f}mm"
                lines.append(line)

            if total_rain >= 25:
                lines.append(f"\n💧 Tổng mưa dự báo: {total_rain:.1f}mm — không cần tưới")
            elif total_rain > 0:
                lines.append(f"\n💧 Tổng mưa dự báo: {total_rain:.1f}mm — có thể lùi lịch tưới")
            else:
                lines.append("\n💧 Không có mưa dự báo — theo dõi độ ẩm đất")

            return "\n".join(lines)

        except Exception as e:
            return f"Lỗi lấy dự báo: {str(e)}"
