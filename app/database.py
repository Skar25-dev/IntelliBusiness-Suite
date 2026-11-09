from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "suite.db"


def get_database_url(cfg=settings) -> str:
    """URL de conexión según `db_type` ('sqlite' por defecto o 'postgresql')."""
    if cfg.db_type == "postgresql":
        return (
            f"postgresql://{cfg.POSTGRES_USER}:{cfg.POSTGRES_PASSWORD}"
            f"@{cfg.POSTGRES_HOST}:{cfg.POSTGRES_PORT}/{cfg.POSTGRES_DB}"
        )
    return f"sqlite:///{DB_PATH}"


SQLALCHEMY_DATABASE_URL = get_database_url()

_connect_args = (
    {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
