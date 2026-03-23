"""
User Profile Tool - Manage farmer plots and profile information in MongoDB.
"""

import datetime
import uuid
from pymongo import MongoClient
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        MONGODB_URL: str = Field(
            default="mongodb://mongodb:27017", description="MongoDB connection URL"
        )
        MONGODB_DB_NAME: str = Field(
            default="bazan_ai", description="MongoDB database name"
        )

    def __init__(self):
        self.valves = self.Valves()
        self._client = None
        self._db = None

    def _get_db(self):
        if self._client is None:
            self._client = MongoClient(self.valves.MONGODB_URL)
            self._db = self._client[self.valves.MONGODB_DB_NAME]
        return self._db

    def upsert_plot(
        self,
        user_id: str,
        crop_type: str,
        location: str,
        area: float,
        soil_type: str,
        recent_activity: str,
    ) -> str:
        """
        Lưu hoặc cập nhật thông tin mảnh đất của nông hộ.
        :param user_id: ID người dùng (lấy từ context hội thoại)
        :param crop_type: Loại cây trồng (ví dụ: Cà phê, Tiêu)
        :param location: Vị trí/Tên mảnh đất (ví dụ: Rẫy 1, Thôn 3)
        :param area: Diện tích (ha)
        :param soil_type: Loại đất (ví dụ: Đất đỏ Bazan)
        :param recent_activity: Hoạt động gần đây (ví dụ: Vừa bón phân đợt 1)
        :return: Thông báo kết quả
        """
        db = self._get_db()
        profiles = db.profiles

        now = datetime.datetime.now()

        # Tìm profile của user
        profile = profiles.find_one({"user_id": user_id})

        if not profile:
            # Tạo mới profile
            new_plot = {
                "plot_id": str(uuid.uuid4()),
                "crop_type": crop_type,
                "location": location,
                "area": area,
                "soil_type": soil_type,
                "recent_activity": recent_activity,
                "updated_at": now,
            }
            profiles.insert_one(
                {
                    "user_id": user_id,
                    "plots": [new_plot],
                    "created_at": now,
                    "updated_at": now,
                }
            )
            return f"Đã tạo hồ sơ mới và lưu mảnh đất tại '{location}' cho người dùng {user_id}."

        # Kiểm tra xem mảnh đất đã tồn tại chưa (dựa trên location)
        existing_plots = profile.get("plots", [])
        plot_index = -1
        for i, plot in enumerate(existing_plots):
            if plot.get("location") == location:
                plot_index = i
                break

        if plot_index >= 0:
            # Cập nhật mảnh đất hiện có
            update_query = {
                f"plots.{plot_index}.crop_type": crop_type,
                f"plots.{plot_index}.area": area,
                f"plots.{plot_index}.soil_type": soil_type,
                f"plots.{plot_index}.recent_activity": recent_activity,
                f"plots.{plot_index}.updated_at": now,
                "updated_at": now,
            }
            profiles.update_one({"user_id": user_id}, {"$set": update_query})
            return f"Đã cập nhật thông tin mảnh đất tại '{location}' cho người dùng {user_id}."
        else:
            # Thêm mảnh đất mới
            new_plot = {
                "plot_id": str(uuid.uuid4()),
                "crop_type": crop_type,
                "location": location,
                "area": area,
                "soil_type": soil_type,
                "recent_activity": recent_activity,
                "updated_at": now,
            }
            profiles.update_one(
                {"user_id": user_id},
                {"$push": {"plots": new_plot}, "$set": {"updated_at": now}},
            )
            return (
                f"Đã thêm mảnh đất mới tại '{location}' vào hồ sơ người dùng {user_id}."
            )

    def list_user_plots(self, user_id: str) -> str:
        """
        Liệt kê danh sách các mảnh đất của người dùng.
        :param user_id: ID người dùng
        :return: Danh sách mảnh đất dạng text hoặc thông báo không tìm thấy
        """
        db = self._get_db()
        profile = db.profiles.find_one({"user_id": user_id})

        if not profile or not profile.get("plots"):
            return f"Người dùng {user_id} chưa có thông tin mảnh đất nào."

        plots = profile["plots"]
        lines = [f"Danh sách mảnh đất của người dùng {user_id}:"]
        for i, plot in enumerate(plots, 1):
            lines.append(
                f"{i}. Vị trí: {plot['location']} | Cây trồng: {plot['crop_type']} | "
                f"Diện tích: {plot['area']}ha | Đất: {plot['soil_type']} | "
                f"Hoạt động: {plot['recent_activity']}"
            )
        return "\n".join(lines)
