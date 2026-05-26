import bcrypt

from shared.database import get_db_connection
from shared.auth import create_token
from shared.rows import row_to_dict
from queries import (
    AUTH_SELECT_USER_BY_EMAIL,
    AUTH_UPDATE_LAST_LOGIN,
    AUTH_SELECT_USER_BY_ID,
)


class AuthService:
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user and return user data if valid."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(AUTH_SELECT_USER_BY_EMAIL, (email,))
                row = cur.fetchone()

                if not row or not bcrypt.checkpw(
                    password.encode("utf-8"), row["password_hash"].encode("utf-8")
                ):
                    return None

                user = row_to_dict(row)
                cur.execute(AUTH_UPDATE_LAST_LOGIN, (user["id"],))
                conn.commit()

        return user

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(AUTH_SELECT_USER_BY_ID, (user_id,))
                row = cur.fetchone()
                return row_to_dict(row)

    @staticmethod
    def create_user_token(user):
        """Create JWT token for user."""
        return create_token(user)
