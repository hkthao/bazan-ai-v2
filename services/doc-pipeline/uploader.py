"""Upload file và chunks vào Open WebUI Knowledge Base."""

import time
import httpx
from config import settings


class WebUIUploader:
    def __init__(self):
        self.base = settings.openwebui_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {settings.openwebui_api_key}"}

    def upload_text_as_file(self, content: str, filename: str) -> str | None:
        """Upload text content như file, trả về file_id."""
        files = {"file": (filename, content.encode("utf-8"), "text/plain")}
        try:
            r = httpx.post(
                f"{self.base}/api/v1/files/",
                headers=self.headers,
                files=files,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["id"]
        except Exception as e:
            print(f"  ERROR upload {filename}: {e}")
            return None

    def wait_for_processing(self, file_id: str, max_wait: int = 30) -> bool:
        """Chờ file được xử lý xong trước khi add vào KB."""
        for _ in range(max_wait // 2):
            try:
                r = httpx.get(
                    f"{self.base}/api/v1/files/{file_id}",
                    headers=self.headers,
                    timeout=10,
                )
                data = r.json()
                if data.get("data", {}).get("content"):
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def add_to_knowledge(self, kb_id: str, file_id: str) -> bool:
        """Add file vào Knowledge Base."""
        try:
            r = httpx.post(
                f"{self.base}/api/v1/knowledge/{kb_id}/file/add",
                headers=self.headers,
                json={"file_id": file_id},
                timeout=30,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            print(f"  ERROR add to KB {kb_id}: {e}")
            return False

    def upload_to_kb(self, content: str, filename: str, kb_id: str) -> str | None:
        """Full flow: upload → wait → add to KB."""
        file_id = self.upload_text_as_file(content, filename)
        if not file_id:
            return None

        if not self.wait_for_processing(file_id):
            print(f"  WARN: {filename} processing timeout")

        if self.add_to_knowledge(kb_id, file_id):
            return file_id
        return None
