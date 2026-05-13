"""SQLite database setup and ORM models."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


DB_PATH = Path(__file__).resolve().parents[1] / "real_estate_advisor.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PropertyAnalysis(Base):
    __tablename__ = "property_analyses"

    id = Column(Integer, primary_key=True, index=True)
    postcode = Column(String, nullable=False)
    region = Column(String, nullable=False)
    property_type = Column(String, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    crime_rate = Column(Float, nullable=False)
    amenity_score = Column(Float, nullable=False)
    hpi_growth = Column(Float, nullable=False)
    distance_to_station = Column(Float, nullable=False)
    predicted_yield = Column(Float, nullable=False)
    investment_score = Column(Float, nullable=False)
    recommendation = Column(String, nullable=False)
    data_sources_used = Column(String, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _apply_lightweight_migrations() -> None:
    """Add new columns if an existing local table was created earlier."""
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(property_analyses)")).fetchall()
        if not columns:
            return

        existing_names = {row[1] for row in columns}
        if "postcode" not in existing_names:
            connection.execute(text("ALTER TABLE property_analyses ADD COLUMN postcode TEXT"))
            connection.execute(text("UPDATE property_analyses SET postcode = 'UNKNOWN' WHERE postcode IS NULL"))
        if "data_sources_used" not in existing_names:
            connection.execute(text("ALTER TABLE property_analyses ADD COLUMN data_sources_used TEXT"))
            connection.execute(
                text("UPDATE property_analyses SET data_sources_used = '[]' WHERE data_sources_used IS NULL")
            )


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def get_db():
    """Yield a database session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

