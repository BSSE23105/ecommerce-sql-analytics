import os
import sys
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

here = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(here, ".env"))


def connect_db():
    # read the login details from .env, never hardcode them
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")

    engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}")

    # create_engine doesn't actually connect, so run a tiny query to make sure the database really answers
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as err:
        logging.error("Could not connect to the database. Check your .env details and that PostgreSQL is running.")
        logging.error("Details: %s", err)
        sys.exit(1)

    return engine
