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


# Database Models matching the new planalytics_database schema
class Calendar(Base):
    """Calendar dimension table"""
    __tablename__ = "calendar"
    
    id = Column(Integer, primary_key=True, index=True)
    end_date = Column(Date, nullable=False)
    year = Column(Integer)
    quarter = Column(Integer)
    month = Column(String(255))
    week = Column(Integer, index=True)
    season = Column(String(255))


class ProductHierarchy(Base):
    """Product hierarchy table - Non-perishable products"""
    __tablename__ = "product_hierarchy"
    
    product_id = Column(Integer, primary_key=True, index=True)
    dept = Column(String(255))
    category = Column(String(255))
    product = Column(String(255), index=True)


class Perishable(Base):
    """Perishable products table"""
    __tablename__ = "perishable"
    
    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(255), index=True)
    perishable_id = Column(Integer)
    min_period = Column(String(255))
    max_period = Column(String(255))
    period_metric = Column(String(255))
    storage = Column(String(255))


class LocationDimension(Base):
    """Location dimension table"""
    __tablename__ = "location"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255), nullable=False, index=True)
    region = Column(String(255), index=True)
    market = Column(String(255))
    state = Column(String(255))
    latitude = Column(Numeric)
    longitude = Column(Numeric)


class EventsData(Base):
    """Events data table"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event = Column(String(255))
    event_type = Column(String(255), index=True)
    event_date = Column(Date, index=True)
    store_id = Column(String(255), index=True)
    region = Column(String(255))
    market = Column(String(255))
    state = Column(String(255))


class WeatherData(Base):
    """Weekly weather data table"""
    __tablename__ = "weekly_weather"
    
    id = Column(Integer, primary_key=True, index=True)
    week_end_date = Column(Date, index=True)
    avg_temp_f = Column(Numeric)
    temp_anom_f = Column(Numeric)
    tmax_f = Column(Numeric)
    tmin_f = Column(Numeric)
    precip_in = Column(Numeric)
    precip_anom_in = Column(Numeric)
    heatwave_flag = Column(Boolean)
    cold_spell_flag = Column(Boolean)
    heavy_rain_flag = Column(Boolean)
    snow_flag = Column(Boolean)
    store_id = Column(String(255), index=True)


class Metrics(Base):
    """Metrics/Sales data table - Contains sales performance data"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(255), index=True)
    location = Column(String(255), index=True)
    end_date = Column(Date, index=True)
    metric = Column(Numeric)
    metric_nrm = Column(Numeric)
    metric_ly = Column(Numeric)


class Sales(Base):
    """Sales transactions table - Individual sales records"""
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    store_code = Column(String(20), nullable=False, index=True)
    product_code = Column(Integer, nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    sales_units = Column(Integer, nullable=False)
    sales_amount = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2))


class Batches(Base):
    """Batch inventory table - Product batches with expiry tracking"""
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    store_code = Column(String(20), nullable=False, index=True)
    product_code = Column(Integer, nullable=False, index=True)
    transaction_date = Column(Date, nullable=False)
    expiry_date = Column(Date, index=True)
    unit_price = Column(Numeric(10, 2))
    total_value = Column(Numeric(10, 2))
    received_qty = Column(Integer)
    mfg_date = Column(Date)
    week_end_date = Column(Date, index=True)
    stock_received = Column(Integer)
    stock_at_week_start = Column(Integer)
    stock_at_week_end = Column(Integer)


class BatchStockTracking(Base):
    """Batch stock tracking table - Detailed transaction-level inventory movements"""
    __tablename__ = "batch_stock_tracking"
    
    record_id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    store_code = Column(String(20), nullable=False, index=True)
    product_code = Column(Integer, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    qty_change = Column(Integer, nullable=False)
    stock_after_transaction = Column(Integer)
    unit_price = Column(Numeric(10, 2))


class SpoilageReport(Base):
    """Spoilage report table - Track product spoilage by batch"""
    __tablename__ = "spoilage_report"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    store_code = Column(String(20), nullable=False, index=True)
    product_code = Column(Integer, nullable=False, index=True)
    qty = Column(Integer, nullable=False)
    spoilage_qty = Column(Integer)
    spoilage_pct = Column(Numeric(5, 2))
    spoilage_case = Column(Integer)


# Legacy aliases for backward compatibility
SalesData = Metrics  # Metrics table contains sales data
InventoryData = Metrics  # No separate inventory table - metrics contains the data


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
