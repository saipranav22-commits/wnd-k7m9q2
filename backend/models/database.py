from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, DateTime, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import DATABASE_URL

Base = declarative_base()

class ActualWindGeneration(Base):
    __tablename__ = "actual_wind_generation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    settlement_period = Column(Integer, nullable=False)
    generation_mw = Column(Float, nullable=False)
    fuel_type = Column(String(20), nullable=False, default="WIND")
    publish_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("start_time", "fuel_type", name="uq_actual_start_fuel"),
        Index("ix_actual_settlement_date_period", "settlement_date", "settlement_period"),
    )

class ForecastWindGeneration(Base):
    __tablename__ = "forecast_wind_generation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publish_time = Column(DateTime, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    generation_mw = Column(Float, nullable=False)
    dataset = Column(String(20), nullable=False, default="WINDFOR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("publish_time", "start_time", name="uq_forecast_pub_start"),
        Index("ix_forecast_lookup", "start_time", "publish_time"),
    )

class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, PARTIAL
    records_ingested = Column(Integer, default=0)
    start_range = Column(String(50), nullable=True)
    end_range = Column(String(50), nullable=True)
    message = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
