import psycopg2
from psycopg2.extras import RealDictCursor
from .config import get_env


def get_db_connection():
    postgres_url = get_env("POSTGRES_URL", required=True)
    return psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)


def real_dict_cursor():
    return RealDictCursor
