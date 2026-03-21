"""Coffee price tool — retrieves current robusta/arabica prices."""

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        PRICE_API_URL: str = Field(
            default="http://data-collector:8002/prices/latest",
            description="URL của price API nội bộ",
        )

    def __init__(self):
        self.valves = self.Valves()

    def get_coffee_price(self, province: str = "") -> str:
        """
        Lấy giá cà phê nhân xô hiện tại.
        :param province: Tên tỉnh (để trống = lấy tất cả)
        :return: Bảng giá dạng text
        """
        import httpx
        try:
            params = {"province": province} if province else {}
            resp = httpx.get(self.valves.PRICE_API_URL, params=params, timeout=10.0)
            data = resp.json()
            lines = ["Giá cà phê nhân xô (VNĐ/kg):"]
            for item in data.get("prices", []):
                lines.append(f"- {item['province']}: {item['price']:,} đ/kg ({item['date']})")
            return "\n".join(lines)
        except Exception as e:
            return f"Lỗi khi lấy giá cà phê: {e}"
