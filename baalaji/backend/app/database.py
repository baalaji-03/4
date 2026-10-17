import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger("pharmacy_app")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

def get_database_engine():
    """
    Creates SQLAlchemy database engine.
    Tries MySQL connection first. If unreachable or DB_TYPE='sqlite', falls back to SQLite.
    """
    if settings.DB_TYPE.lower() == "sqlite":
        if os.getenv("VERCEL"):
            raise RuntimeError("SQLite is not persistent on Vercel. Configure a hosted MySQL DATABASE_URL.")
        logger.info("Using SQLite database as configured.")
        return create_engine(
            "sqlite:///./pharmacy.db",
            connect_args={"check_same_thread": False}
        )

    if os.getenv("VERCEL"):
        database_url = settings.DATABASE_URL
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        logger.info("Connecting to configured hosted MySQL database.")
        return create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=1,
            max_overflow=0
        )
    
    try:
        # Test connecting to MySQL
        logger.info(f"Connecting to MySQL at {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}...")
        mysql_engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        with mysql_engine.connect():
            pass  # Ping check
        logger.info("Successfully connected to MySQL database.")
        return mysql_engine
    except Exception as e:
        logger.warning(
            f"MySQL connection to {settings.MYSQL_HOST}:{settings.MYSQL_PORT} failed ({e}). "
            f"Falling back to local SQLite database (pharmacy.db) for uninterrupted operation."
        )
        return create_engine(
            "sqlite:///./pharmacy.db",
            connect_args={"check_same_thread": False}
        )

engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
