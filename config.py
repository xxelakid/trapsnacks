
import os


def get_database_url():
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        if os.environ.get("REQUIRE_PERSISTENT_DB") == "1":
            raise RuntimeError("DATABASE_URL is required")
        return "sqlite:///trapsnacks.db"

    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]

    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "local-development-only-change-me"
    )

    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    # A delivery order's meal must be ready this many minutes after the chef taps
    # "Start preparing". The countdown shows on the kitchen, rider and delivery screens.
    PREP_MINUTES = 10
    NO_RIDER_ALERT_MINUTES = 2
