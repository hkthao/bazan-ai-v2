import unittest
from unittest.mock import patch
import mongomock
from services.pipelines.tools.user_profile_tool import Tools


class TestUserProfileTool(unittest.TestCase):
    def setUp(self):
        self.tool = Tools()
        # Mock MongoClient with mongomock
        self.mock_client = mongomock.MongoClient()
        # Patch the MongoClient to return our mock_client
        self.patcher = patch(
            "services.pipelines.tools.user_profile_tool.MongoClient",
            return_value=self.mock_client,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_upsert_multi_plots(self):
        user_id = "test_user_123"

        # 1. Lưu mảnh đất thứ nhất
        res1 = self.tool.upsert_plot(
            user_id=user_id,
            crop_type="Cà phê Robusta",
            location="Rẫy Thôn 1",
            area=1.5,
            soil_type="Đất đỏ Bazan",
            recent_activity="Bón phân đợt 1",
        )
        self.assertIn("Đã tạo hồ sơ mới", res1)

        # 2. Lưu mảnh đất thứ hai (khác location)
        res2 = self.tool.upsert_plot(
            user_id=user_id,
            crop_type="Tiêu",
            location="Vườn sau nhà",
            area=0.5,
            soil_type="Đất sét pha cát",
            recent_activity="Tưới nước đợt đầu",
        )
        self.assertIn("Đã thêm mảnh đất mới", res2)

        # 3. Kiểm tra DB: phải có 2 mảnh đất
        db = self.mock_client[self.tool.valves.MONGODB_DB_NAME]
        profile = db.profiles.find_one({"user_id": user_id})
        self.assertIsNotNone(profile)
        self.assertEqual(len(profile["plots"]), 2)

        # 4. Kiểm tra cập nhật mảnh đất hiện có (cùng location)
        res3 = self.tool.upsert_plot(
            user_id=user_id,
            crop_type="Cà phê Robusta (Cải tạo)",
            location="Rẫy Thôn 1",
            area=1.5,
            soil_type="Đất đỏ Bazan",
            recent_activity="Đã thu hoạch xong",
        )
        self.assertIn("Đã cập nhật thông tin mảnh đất", res3)

        # 5. Kiểm tra DB: vẫn chỉ có 2 mảnh đất nhưng nội dung mảnh 1 thay đổi
        profile_updated = db.profiles.find_one({"user_id": user_id})
        self.assertEqual(len(profile_updated["plots"]), 2)

        plot1 = next(
            p for p in profile_updated["plots"] if p["location"] == "Rẫy Thôn 1"
        )
        self.assertEqual(plot1["crop_type"], "Cà phê Robusta (Cải tạo)")
        self.assertEqual(plot1["recent_activity"], "Đã thu hoạch xong")

    def test_list_plots(self):
        user_id = "test_user_456"
        # Thêm 2 mảnh đất
        self.tool.upsert_plot(user_id, "Cà phê", "Lô A", 1.0, "Đất đỏ", "Nghỉ")
        self.tool.upsert_plot(user_id, "Tiêu", "Lô B", 0.5, "Đất vàng", "Tưới")

        # Liệt kê
        res = self.tool.list_user_plots(user_id)
        self.assertIn("Lô A", res)
        self.assertIn("Lô B", res)
        self.assertIn("Cà phê", res)
        self.assertIn("Tiêu", res)


if __name__ == "__main__":
    unittest.main()
