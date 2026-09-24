import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db import Base

class RoleEnum(str, enum.Enum):
    farmer = "farmer"
    admin = "admin"

class SoilTypeEnum(str, enum.Enum):
    sandy_loam = "sandy_loam"
    clay = "clay"
    loam = "loam"
    silt_loam = "silt_loam"

class SourceEnum(str, enum.Enum):
    simulated = "simulated"
    real = "real"

class ChannelEnum(str, enum.Enum):
    app = "app"
    sms = "sms"

class ModelNameEnum(str, enum.Enum):
    triage = "triage"
    disease = "disease"
    nutrient = "nutrient"
    sensor = "sensor"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.farmer)
    
    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")

class Farm(Base):
    __tablename__ = "farms"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    soil_type: Mapped[SoilTypeEnum] = mapped_column(SAEnum(SoilTypeEnum), nullable=False)
    
    user = relationship("User", back_populates="farms")
    readings = relationship("SensorReading", back_populates="farm", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="farm", cascade="all, delete-orphan")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farms.id"), nullable=False)
    soil_moisture: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    leaf_wetness: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[SourceEnum] = mapped_column(SAEnum(SourceEnum), nullable=False, default=SourceEnum.simulated)
    
    farm = relationship("Farm", back_populates="readings")

class Checkin(Base):
    __tablename__ = "checkins"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farms.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    farm = relationship("Farm", back_populates="checkins")
    predictions = relationship("Prediction", back_populates="checkin", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checkins.id"), nullable=False)
    reading_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sensor_readings.id"), nullable=True)
    triage_result: Mapped[str] = mapped_column(Text, nullable=False)
    disease_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    disease_conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    sensor_conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrient_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrient_conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_versions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    checkin = relationship("Checkin", back_populates="predictions")
    reading = relationship("SensorReading")
    alerts = relationship("Alert", back_populates="prediction", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="prediction", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    farm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farms.id"), nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[ChannelEnum] = mapped_column(SAEnum(ChannelEnum), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    prediction = relationship("Prediction", back_populates="alerts")
    farm = relationship("Farm")

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    accurate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    useful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    correct_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    prediction = relationship("Prediction", back_populates="feedback")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[ModelNameEnum] = mapped_column(SAEnum(ModelNameEnum), nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

class RetrainingJob(Base):
    __tablename__ = "retraining_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    old_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    new_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    passed_gate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deployed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
