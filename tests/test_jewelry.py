import io
from pathlib import Path
import pytest
from PIL import Image
from fastapi import UploadFile

from app.models.schemas import JewelryPlannerInput
from app.services.recommendation_service import recommendation_service
from app.services.image_service import image_service


def test_jewelry_planner_without_image():
    input_data = JewelryPlannerInput(
        budget=10000.0,
        currency="INR",
        occasion="Wedding / Marriage",
        jewelry_type="Complete Set",
        style_preference="Traditional",
        metal_preference="Gold Plated",
        color_preference="Ruby Red"
    )

    plan = recommendation_service.process_jewelry_plan(input_data=input_data)

    assert plan is not None
    assert plan.planner_type == "jewelry"
    assert plan.original_budget == 10000.0
    assert plan.total_estimated_cost <= 10000.0
    assert plan.remaining_budget >= 0.0
    assert len(plan.items) > 0


def test_jewelry_planner_with_image(tmp_path):
    # Create a test outfit image using PIL
    test_img = Image.new("RGB", (300, 300), color=(180, 20, 50))  # Maroon outfit
    img_byte_arr = io.BytesIO()
    test_img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    # Save to temp path
    test_img_path = tmp_path / "test_outfit.png"
    with open(test_img_path, "wb") as f:
        f.write(img_bytes)

    input_data = JewelryPlannerInput(
        budget=15000.0,
        currency="INR",
        occasion="Wedding / Marriage",
        jewelry_type="Complete Set",
        style_preference="Antique Kundan",
        metal_preference="Gold Plated",
        color_preference="Maroon"
    )

    plan = recommendation_service.process_jewelry_plan(
        input_data=input_data,
        image_path=test_img_path,
        image_url="/static/uploads/test_outfit.png"
    )

    assert plan is not None
    assert plan.total_estimated_cost <= 15000.0
    assert plan.outfit_image_url == "/static/uploads/test_outfit.png"
    assert plan.outfit_analysis is not None


def test_image_validation_rejection():
    # Test text file as fake image
    fake_file = io.BytesIO(b"this is not an image file")
    upload = UploadFile(filename="fake.txt", file=fake_file)
    upload.headers = {"content-type": "text/plain"}

    with pytest.raises(Exception):
        image_service.validate_and_save_upload(upload)
