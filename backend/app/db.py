import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)

def get_engine():
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "shipsense"),
        query={"charset": "utf8mb4"}
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)

engine = get_engine()

def query(sql, params=None):
    with engine.connect() as connection:
        result = connection.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]

def test_connection():
    with engine.connect() as connection:
        return dict(connection.execute(
            text("SELECT DATABASE() AS db, VERSION() AS version")
        ).mappings().one())

if __name__ == "__main__":
    print("Testing MySQL connection...")
    print(test_connection())
    print("MySQL connection successful!")
