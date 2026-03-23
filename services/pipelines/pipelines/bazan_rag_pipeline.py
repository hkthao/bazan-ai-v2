"""Bazan AI RAG Pipeline — injects knowledge context before LLM call."""

from typing import Optional
import httpx


class Pipeline:
    def __init__(self):
        self.name = "Bazan AI RAG Pipeline"
        self.rag_api_url = "http://rag-api:8001"

    async def on_startup(self):
        print(f"[Bazan Pipeline] started — RAG API: {self.rag_api_url}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Intercept request, fetch relevant context, inject into system prompt."""
        query = body.get("messages", [{}])[-1].get("content", "")
        if not query:
            return body

        context = await self._fetch_context(query)
        if context:
            system_msg = {
                "role": "system",
                "content": (
                    "Bạn là trợ lý chuyên gia về cà phê Tây Nguyên (Bazan AI). "
                    "Nhiệm vụ của bạn là tư vấn kỹ thuật canh tác, giá cả và thời tiết.\n\n"
                    "QUY TẮC QUẢN LÝ NÔNG HỘ:\n"
                    "1. Khi người dùng cung cấp thông tin về mảnh đất (loại cây, diện tích, vị trí, loại đất, hoạt động), "
                    "hãy sử dụng công cụ 'upsert_plot' để lưu lại hồ sơ. "
                    "Luôn xác nhận với người dùng sau khi lưu thành công.\n"
                    "2. Nếu người dùng có nhiều mảnh đất, hãy sử dụng 'list_user_plots' để liệt kê danh sách "
                    "và hỏi họ đang muốn nhận tư vấn cho mảnh đất cụ thể nào.\n"
                    "3. Ưu tiên sử dụng kiến thức từ tài liệu RAG dưới đây để trả lời:\n\n"
                    + context
                ),
            }
            body["messages"] = [system_msg] + body.get("messages", [])
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        return body

    async def _fetch_context(self, query: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    f"{self.rag_api_url}/search",
                    json={"query": query, "top_k": 5},
                )
                results = resp.json().get("results", [])
                return "\n\n".join(f"[{r['source']}]\n{r['content']}" for r in results)
            except Exception as e:
                print(f"[Bazan Pipeline] RAG fetch failed: {e}")
                return ""
