"""Farming plan tool — generates cultivation schedule based on inputs."""

from pydantic import BaseModel


class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def create_farming_plan(
        self, province: str, area_ha: float, current_month: int
    ) -> str:
        """
        Tạo kế hoạch trồng trọt cà phê dựa theo địa điểm và thời điểm hiện tại.
        :param province: Tỉnh trồng cà phê
        :param area_ha: Diện tích (ha)
        :param current_month: Tháng hiện tại (1-12)
        :return: Kế hoạch canh tác dạng text
        """
        # Placeholder — logic sẽ được implement trong issue tiếp theo
        return (
            f"Kế hoạch canh tác cà phê tại {province}, "
            f"diện tích {area_ha} ha, tháng {current_month}:\n"
            "[Nội dung sẽ được bổ sung từ knowledge base]"
        )
