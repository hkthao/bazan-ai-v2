"""Soil and nutrition lookup tool for Tay Nguyen coffee farming."""

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def get_soil_info(self, province: str) -> str:
        """
        Tra cứu thông tin đất đai và dinh dưỡng phù hợp cho cà phê tại tỉnh.
        :param province: Tên tỉnh Tây Nguyên
        :return: Thông tin đất đai dạng text
        """
        # Placeholder — sẽ đọc từ seeds/soil_types.json
        return f"Thông tin đất đai tỉnh {province}: [sẽ được bổ sung]"
