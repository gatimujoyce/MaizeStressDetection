import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from app.services.fusion import compute_severity
from app.services.recommend import get_recommendation
from app.routers.checkins import checkin_and_predict
from fastapi import UploadFile, HTTPException
from app.models import User, Farm, SensorReading
from io import BytesIO

@pytest.mark.asyncio
async def test_compute_severity_matrix_1():
    # 1. Low confidence -> Inconclusive
    res = compute_severity("Common Rust", 0.5, "Normal", 0.8, 2.0, "in_scope")
    assert res == "Inconclusive"

@pytest.mark.asyncio
async def test_compute_severity_matrix_2():
    # 2. Out of scope -> Inconclusive
    res = compute_severity("Common Rust", 0.9, "Normal", 0.8, 2.0, "out_of_scope")
    assert res == "Inconclusive"

@pytest.mark.asyncio
async def test_compute_severity_matrix_3():
    # 3. Healthy + Normal -> Low
    res = compute_severity("Healthy", 0.9, "Normal", 0.8, 2.0, "in_scope")
    assert res == "Low"

@pytest.mark.asyncio
async def test_compute_severity_matrix_4():
    # 4. Healthy + Drought Stress -> Medium
    res = compute_severity("Healthy", 0.9, "Drought Stress", 0.8, 2.0, "in_scope")
    assert res == "Medium"

@pytest.mark.asyncio
async def test_compute_severity_matrix_5():
    # 5. Common Rust + Waterlogging Risk -> High
    res = compute_severity("Common Rust", 0.9, "Waterlogging Risk", 0.8, 4.0, "in_scope")
    assert res == "High"

@pytest.mark.asyncio
async def test_compute_severity_matrix_6():
    # 6. Northern Leaf Blight + Normal (lw < 3) -> High
    res = compute_severity("Northern Leaf Blight", 0.9, "Normal", 0.8, 2.0, "in_scope")
    assert res == "High"

@pytest.mark.asyncio
async def test_compute_severity_matrix_7():
    # 7. Northern Leaf Blight + Normal (lw >= 3) -> Medium
    res = compute_severity("Northern Leaf Blight", 0.9, "Normal", 0.8, 4.0, "in_scope")
    assert res == "Medium"

@pytest.mark.asyncio
async def test_compute_severity_matrix_8():
    # 8. Gray Leaf Spot + Heat Stress -> High
    res = compute_severity("Gray Leaf Spot", 0.9, "Heat Stress", 0.8, 2.0, "in_scope")
    assert res == "High"

@pytest.mark.asyncio
async def test_compute_severity_matrix_9():
    # 9. Gray Leaf Spot + Normal (lw >= 2) -> Medium
    res = compute_severity("Gray Leaf Spot", 0.9, "Normal", 0.8, 3.0, "in_scope")
    assert res == "Medium"

@pytest.mark.asyncio
async def test_endpoint_predict_flow_high_severity():
    # 10. Test endpoint integration with high severity triggers SMS
    mock_db = AsyncMock()

    # Create the farm and user first
    mock_user = User(
        id=uuid.uuid4(),
        name="Test User",
        phone="+254700000000",
        password_hash="hash",
    )

    farm_id = uuid.uuid4()

    farm = Farm(
        id=farm_id,
        user_id=mock_user.id,
        name="Test Farm",
        location="Loc",
        soil_type="loam",
    )

    sensor_reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=farm_id,
        soil_moisture=30.0,
        temperature=24.0,
        humidity=55.0,
        leaf_wetness=2.0,
    )

    # Configure execute() to return normal SQLAlchemy-style result objects
    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = farm

    sensor_result = MagicMock()
    sensor_result.scalar_one_or_none.return_value = sensor_reading

    mock_db.execute = AsyncMock(
        side_effect=[farm_result, sensor_result]
    )

    # AsyncSession.add() is synchronous
    mock_db.add = MagicMock()
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = BytesIO(b"fake image content")
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpeg"
    
    mock_user = User(id=uuid.uuid4(), name="Test User", phone="+254700000000", password_hash="hash")
    
    with patch("app.routers.checkins.os.path.join", return_value="fake/path.jpg"), \
         patch("app.routers.checkins.open"), \
         patch("app.routers.checkins.send_sms", return_value={"SMSMessageData": {"Message": "SentTo1"}}) as mock_send_sms:
        
        result = await checkin_and_predict(uuid.uuid4(), mock_file, mock_user, mock_db)
        
        assert result.severity == "High"
        assert result.recommendation is not None
        assert result.model_versions["inference_mode"] == "demo"
        mock_send_sms.assert_called_once()
        assert "+254700000000" in mock_send_sms.call_args[0]
