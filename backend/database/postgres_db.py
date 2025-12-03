from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Text, Boolean, TIMESTAMP, Date, Numeric
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
    __tablename__ = "calendar"
    
    year = Column(Integer)
    quarter = Column(Integer)
    month = Column(String(255))
    week = Column(Integer, primary_key=True, index=True)
    end_date = Column(Date)
    season = Column(String(255))


class ProductHierarchy(Base):
    """Product hierarchy table"""
    __tablename__ = "product_hierarchy"
    
    product_id = Column(Integer, primary_key=True, index=True)
    dept = Column(String(255))
    category = Column(String(255))
    product = Column(String(255), index=True)
    min_period = Column(String(255))
    max_period = Column(Float)
    period_metric = Column(String(255))
    storage = Column(String(255))
    uom = Column(String(255))
    unit_price = Column(Float)


class LocationDimension(Base):
    """Location dimension table"""
    __tablename__ = "location"
    
    location = Column(String(255), primary_key=True, index=True)
    region = Column(String(255), index=True)
    market = Column(String(255))
    state = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)


class EventsData(Base):
    """Events data table"""
    __tablename__ = "events"
    
    event = Column(String(255), primary_key=True)
    event_type = Column(String(255), index=True)
    event_date = Column(Date, primary_key=True, index=True)
    store_id = Column(String(255), primary_key=True, index=True)
    region = Column(String(255))
    market = Column(String(255))
    state = Column(String(255))


class WeatherData(Base):
    """Weather data table"""
    __tablename__ = "weekly_weather"
    
    week_end_date = Column(Date, primary_key=True, index=True)
    store_id = Column(String(255), primary_key=True, index=True)
    avg_temp_f = Column(Numeric)
    temp_anom_f = Column(Numeric)
    tmax_f = Column(Integer)
    tmin_f = Column(Integer)
    precip_in = Column(Numeric)
    precip_anom_in = Column(String(255))
    heatwave_flag = Column(Boolean)
    cold_spell_flag = Column(Boolean)
    heavy_rain_flag = Column(Boolean)
    snow_flag = Column(Boolean)


class InventoryData(Base):
    """Inventory data table"""
    __tablename__ = "inventory"
    
    store_id = Column(String(255), primary_key=True, index=True)
    product_id = Column(Integer, primary_key=True, index=True)
    end_date = Column(Date, primary_key=True, index=True)
    begin_on_hand_units = Column(Integer)
    received_units = Column(Integer)
    sales_units = Column(Integer)
    end_on_hand_units = Column(Integer)
    base_stock_units = Column(Integer)
    days_of_supply_end = Column(Numeric)
    stock_status = Column(String(255))


class Metrics(Base):
    """Metrics/Sales data table"""
    __tablename__ = "metrics"
    
    product = Column(String(255), primary_key=True, index=True)
    location = Column(String(255), primary_key=True, index=True)
    end_date = Column(Date, primary_key=True, index=True)
    metric = Column(Integer)
    metric_nrm = Column(Integer)
    metric_ly = Column(Integer)


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
