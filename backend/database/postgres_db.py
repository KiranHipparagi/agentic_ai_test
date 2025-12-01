from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Text, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from core.config import settings
from core.logger import logger
import sqlalchemy

# SQLAlchemy setup for PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models matching your PostgreSQL schema
class Calendar(Base):
    __tablename__ = "cal"
    
    year = Column(BigInteger)
    quarter = Column(BigInteger)
    month = Column(Text)
    week = Column(BigInteger, primary_key=True, index=True)
    end_date = Column(TIMESTAMP)


class ProductHierarchy(Base):
    __tablename__ = "phier"
    
    product_id = Column(BigInteger, primary_key=True, index=True)
    dept = Column(Text)
    category = Column(Text)
    product = Column(Text, index=True)
    min_period = Column(Text)
    max_period = Column(Float)
    period_metric = Column(Text)
    storage = Column(Text)
    uom = Column(Text)
    unit_price = Column(Float)


class LocationDimension(Base):
    __tablename__ = "locdim"
    
    location = Column(Text, primary_key=True, index=True)
    region = Column(Text, index=True)
    market = Column(Text)
    state = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)


class EventsData(Base):
    __tablename__ = "events"
    
    event = Column(Text, primary_key=True)
    event_type = Column(Text, index=True)
    event_date = Column(Text, index=True)
    store_id = Column(Text, index=True)
    region = Column(Text)
    market = Column(Text)
    state = Column(Text)


class WeatherData(Base):
    __tablename__ = "weather"
    
    week_end_date = Column(TIMESTAMP, primary_key=True, index=True)
    store_id = Column(Text, primary_key=True, index=True)
    avg_temp_f = Column(Float)
    temp_anom_f = Column(Float)
    tmax_f = Column(BigInteger)
    tmin_f = Column(BigInteger)
    precip_in = Column(Float)
    precip_anom_in = Column(Float)
    heatwave_flag = Column(Boolean)
    cold_spell_flag = Column(Boolean)
    heavy_rain_flag = Column(Boolean)
    snow_flag = Column(Boolean)


class InventoryData(Base):
    __tablename__ = "inventory"
    
    store_id = Column(Text, primary_key=True, index=True)
    product_id = Column(BigInteger, primary_key=True, index=True)
    end_date = Column(TIMESTAMP, primary_key=True, index=True)
    begin_on_hand_units = Column(BigInteger)
    received_units = Column(BigInteger)
    sales_units = Column(BigInteger)
    end_on_hand_units = Column(BigInteger)
    base_stock_units = Column(BigInteger)
    days_of_supply_end = Column(Float)
    stock_status = Column(Text)


class Metrics(Base):
    __tablename__ = "metrics"
    
    product = Column(Text)
    location = Column(Text, index=True)
    end_date = Column(Text, index=True)
    metric = Column(BigInteger)
    metric_nrm = Column(BigInteger)
    metric_ly = Column(BigInteger)  # Added based on new logic
    product_id = Column(BigInteger, primary_key=True, index=True)
    column1 = Column(Float)


# Legacy aliases for backward compatibility
SalesData = Metrics  # Metrics table contains sales data


def init_db():
    """Initialize database connection - tables already exist in PostgreSQL"""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("✅ PostgreSQL database connection established")
        logger.info(f"📊 Connected to: {settings.POSTGRES_DB} at {settings.POSTGRES_SERVER}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        raise


@contextmanager
def get_db() -> Session:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()
