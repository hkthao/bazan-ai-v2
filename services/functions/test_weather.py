"""Test script chạy local để verify weather function trước khi upload lên WebUI."""

import os
import sys
from pathlib import Path

# Add current dir to path to import weather_tool
sys.path.insert(0, str(Path(__file__).parent))

from weather_tool import Tools


def test_all_provinces():
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        print("FAIL: Cần set OPENWEATHER_API_KEY trong môi trường")
        print("      Đăng ký tại: https://openweathermap.org/api")
        return

    tool = Tools()
    tool.valves.OPENWEATHER_API_KEY = api_key

    provinces = [
        "đắk lắk",
        "Lâm Đồng",
        "gia lai",
        "Kon Tum",
        "dak nong",
        "buôn ma thuột",  # alias
        "pleiku",  # alias
        "tỉnh không tồn tại",  # edge case
    ]

    print("=" * 50)
    print("Test Weather Function — Bazan AI")
    print("=" * 50)

    for p in provinces:
        print(f"\n[Test] '{p}'")
        print("-" * 40)
        result = tool.get_weather(p)
        print(result)

    print("\n" + "=" * 50)
    print("Test forecast Đắk Lắk:")
    print("-" * 40)
    print(tool.get_forecast("đắk lắk"))


if __name__ == "__main__":
    test_all_provinces()
