import io
import uuid
import httpx
import pytest
from bs4 import BeautifulSoup
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"


def get_test_client():
    try:
        with httpx.Client(base_url=BASE_URL, timeout=1.0) as probe:
            res = probe.get("/health")
            if res.status_code == 200:
                return httpx.Client(base_url=BASE_URL, follow_redirects=True, timeout=30.0)
    except Exception:
        pass

    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import init_db
    init_db()
    return TestClient(app, follow_redirects=True)


def test_live_server_e2e():
    # Use client with cookie jar
    with get_test_client() as client:
        # 1. Test Health & Landing Page
        res_health = client.get("/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert health_data["status"] == "healthy"
        print("✓ /health passed")

        res_landing = client.get("/")
        assert res_landing.status_code == 200
        assert "PocketSmart" in res_landing.text
        assert "Home Interior Planner" in res_landing.text
        assert "Party Budget Planner" in res_landing.text
        assert "Jewelry & Styling" in res_landing.text
        print("✓ Landing page rendered successfully")

        # 2. Test User Registration
        unique_username = f"aarav_{uuid.uuid4().hex[:6]}"
        reg_payload = {
            "full_name": "Aarav Sharma",
            "email": f"{unique_username}@example.com",
            "username": unique_username,
            "password": "Password@123",
            "confirm_password": "Password@123"
        }
        res_reg = client.post("/register", data=reg_payload)
        assert res_reg.status_code == 200
        assert "Aarav Sharma" in res_reg.text
        assert "Dashboard" in res_reg.text
        print("✓ Registration and session redirect to /dashboard passed")

        # 3. Test Dashboard Page
        res_dash = client.get("/dashboard")
        assert res_dash.status_code == 200
        assert "Total Plans" in res_dash.text
        assert "Aarav Sharma" in res_dash.text
        print("✓ Dashboard view passed")

        # 4. Test Home Interior Planner Form & Generation
        res_home_page = client.get("/home-planner")
        assert res_home_page.status_code == 200
        assert "Home Interior" in res_home_page.text

        home_form_data = {
            "budget": "100000",
            "currency": "INR",
            "living_room": "true",
            "bedroom_count": "2",
            "kitchen": "true",
            "dining_room": "true",
            "lights_count": "10",
            "fans_count": "3",
            "dining_table_count": "1",
            "furniture_requirements": "Sectional sofa and king bed",
            "decor_requirements": "Canvas art and rugs",
            "preferred_style": "Modern",
            "color_preferences": "Warm Neutral",
            "additional_requirements": "Focus on high durability"
        }
        res_home_gen = client.post("/generate-home", data=home_form_data)
        assert res_home_gen.status_code == 200
        assert "Curated Recommendations" in res_home_gen.text
        assert "100,000" in res_home_gen.text
        assert "Amazon" in res_home_gen.text or "IKEA" in res_home_gen.text
        print("✓ Home Interior Planner generation passed")

        # 5. Test Party Planner Form & Generation
        res_party_page = client.get("/party-planner")
        assert res_party_page.status_code == 200

        party_form_data = {
            "budget": "75000",
            "currency": "INR",
            "guest_count": "50",
            "event_type": "Birthday Party",
            "city_location": "Chennai",
            "catering_required": "true",
            "venue_required": "true",
            "decoration_required": "true",
            "cake_required": "true",
            "entertainment_required": "true",
            "food_preference": "Multi-Cuisine",
            "additional_requirements": "Evening lighting"
        }
        res_party_gen = client.post("/generate-party", data=party_form_data)
        assert res_party_gen.status_code == 200
        assert "75,000" in res_party_gen.text
        assert "Catering" in res_party_gen.text or "Party" in res_party_gen.text
        print("✓ Party Planner generation passed")

        # 6. Test Jewelry Planner without image
        jewelry_form_data = {
            "budget": "10000",
            "currency": "INR",
            "occasion": "Wedding / Marriage",
            "jewelry_type": "Complete Coordinated Set",
            "style_preference": "Traditional",
            "metal_preference": "Gold Plated",
            "color_preference": "Ruby Red",
            "additional_requirements": "Choker set preferred"
        }
        res_jewelry_gen = client.post("/generate-jewelry", data=jewelry_form_data)
        assert res_jewelry_gen.status_code == 200
        assert "10,000" in res_jewelry_gen.text
        assert "Necklace" in res_jewelry_gen.text or "Jewelry" in res_jewelry_gen.text
        print("✓ Jewelry Planner without image passed")

        # 7. Test Jewelry Planner WITH outfit image upload
        img = Image.new("RGB", (250, 250), color=(160, 30, 45))  # Maroon dress
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        files = {
            "outfit_image": ("maroon_saree.jpg", img_io, "image/jpeg")
        }
        jewelry_img_data = {
            "budget": "12000",
            "currency": "INR",
            "occasion": "Reception Gala",
            "jewelry_type": "Complete Coordinated Set",
            "style_preference": "Antique Kundan",
            "metal_preference": "Gold Plated",
            "color_preference": "Maroon and Gold",
            "additional_requirements": "Matching bridal earrings"
        }
        res_jewelry_img = client.post("/generate-jewelry", data=jewelry_img_data, files=files)
        assert res_jewelry_img.status_code == 200
        assert "12,000" in res_jewelry_img.text
        assert "/static/uploads/" in res_jewelry_img.text
        print("✓ Jewelry Planner WITH outfit image upload passed")

        # 8. Test Recommendation History Page
        res_history = client.get("/history")
        assert res_history.status_code == 200
        assert "Recommendation History" in res_history.text
        assert "Home Interior" in res_history.text
        assert "Party" in res_history.text
        print("✓ Recommendation History page and saved records passed")

        # 9. Test Session Data & Session Info Endpoints
        res_sess_info = client.get("/session-info")
        assert res_sess_info.status_code == 200
        sess_info = res_sess_info.json()
        assert sess_info["authenticated"] is True
        assert sess_info["user"]["username"] == unique_username

        res_sess_data = client.get("/session-data")
        assert res_sess_data.status_code == 200
        sess_data = res_sess_data.json()
        assert sess_data["authenticated"] is True
        assert sess_data["email"] == f"{unique_username}@example.com"
        print("✓ /session-info and /session-data API endpoints passed")

        # 10. Test Logout
        res_logout = client.get("/logout")
        assert res_logout.status_code == 200
        assert "Sign In" in res_logout.text

        # 11. Test Protected History redirect after logout
        res_hist_unauth = client.get("/history")
        assert res_hist_unauth.status_code == 200
        assert "Sign In" in res_hist_unauth.text  # Redirected to login
        print("✓ Logout and session teardown passed")


if __name__ == "__main__":
    test_live_server_e2e()
    print("\n🎉 ALL LIVE SERVER END-TO-END TESTS PASSED SUCCESSFULLY!")
