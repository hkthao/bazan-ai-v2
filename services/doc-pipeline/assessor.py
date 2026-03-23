"""LLM đánh giá chất lượng tài liệu dùng Ollama local."""

import json
import re
import time
from config import settings

ASSESS_PROMPT = """Phân tích tài liệu cà phê sau và trả về JSON hợp lệ.
Chỉ trả về JSON, không có text khác, không có markdown code block.

{{
  "quality_score": <số nguyên 1-10>,
  "reason": "<lý do ngắn gọn 1-2 câu>",
  "topic": "<một trong: canh_tac|benh_hai|thu_hoach|che_bien|kinh_te|khi_hau|giong_cay|khac>",
  "region": "<một trong: tay_nguyen|dak_lak|lam_dong|gia_lai|kon_tum|dak_nong|chung>",
  "language": "<vi|en|other>",
  "doc_type": "<một trong: bao_cao|huong_dan|nghien_cuu|tin_tuc|du_lieu|khac>"
}}

Tiêu chí quality_score:
- 8-10: Có số liệu cụ thể, nguồn rõ ràng, thực hành được, liên quan trực tiếp cây cà phê
- 5-7:  Thông tin đúng nhưng chung chung hoặc thiếu chi tiết thực hành
- 3-4:  Thông tin sơ sài, lỗi thời hoặc chỉ liên quan gián tiếp
- 1-2:  Không liên quan, sai lệch, hoặc chất lượng rất kém

--- BẮT ĐẦU TÀI LIỆU ---
{text}
--- KẾT THÚC TÀI LIỆU ---"""


def assess(text: str, max_retries: int = 3) -> dict:
    """Gửi 8000 kí tự đầu đến LLM để đánh giá."""
    import ollama

    truncated = text[:8000]  # ~2000 tokens

    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model=settings.assess_model,
                messages=[
                    {
                        "role": "user",
                        "content": ASSESS_PROMPT.format(text=truncated),
                    }
                ],
                options={
                    "num_ctx": settings.assess_context,
                    "temperature": 0.1,
                },
            )
            raw = response["message"]["content"].strip()

            # Strip markdown code block nếu có
            raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

            result = json.loads(raw)

            # Validate required fields
            required = ["quality_score", "reason", "topic", "region", "language", "doc_type"]
            for field in required:
                if field not in result:
                    raise ValueError(f"Missing field: {field}")

            result["quality_score"] = int(result["quality_score"])
            if not 1 <= result["quality_score"] <= 10:
                raise ValueError(f"quality_score out of range: {result['quality_score']}")

            return result

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"  WARN: assess attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    # Fallback nếu tất cả retry fail
    return {
        "quality_score": 5,
        "reason": "Không thể đánh giá tự động — cần xem thủ công",
        "topic": "khac",
        "region": "chung",
        "language": "vi",
        "doc_type": "khac",
    }
