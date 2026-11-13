import os
import sys
from logging.config import fileConfig

from alembic import context

from app.core.config import settings
from app.models import Base
from app.models.farm import Farm
from app.models.outbreak import Outbreak
from app.models.alert import Alert

if sys.version_info >= (3, 8):
    import importlib.metadata as import_metadata
else:
    import importlib_metadata as import_metadata


config = context.config
config.set("script_location", "alembic")
config.set("version_path", "alembic/versions")

config.set(
    "prepend_sys_path", str(os.path.join("..", ".."))
)

config.set(
    "sqlalchemy.url",
    os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/poultry_disease"),
)

try:
    if config.config_section_name in config.get_section_names():
        raise Exception(f"Section {config.config_section_name} is already defined")
    from logging.config import fileConfig

    fileConfig("alembic", defaults={"loggers": [], "handlers": [], "formatters": []})
except Exception:
    pass

sys.path.insert(0, os.path.dirname(__file__))


def run_migrations_offline() -> None:
    """This branch is used by Alembic's offline mode."""
    context.configure(
        url=config.get_section(config.config_section_name).get("sqlalchemy.url", "postgresql+asyncpg://"),
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_from_connect() -> None:
    """This branch is used by Alembic's online mode."""
    connectable = getattr(context, "connectable", None)
    if connectable is False:
        # Alembic needs to connect to the database with the same engine
        # used to create the alembic env.
        raise Exception("This environment does not support Alembic's connectable")
    context.configure(
        url=config.get_section(config.config_section_name).get("sqlalchemy.url", "postgresql+asyncpg://"),
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def is_offline() -> bool:
    return getattr(context, "is_offline_mode", False)


def get_context() -> context.Context:
    return context.get_context()


def get_url() -> str:
    return config.get_section(config.config_section_name).get("sqlalchemy.url", "postgresql+asyncpg://")


def set_url(url: str) -> None:
    config.get_section(config.config_section_name)["sqlalchemy.url"] = url


def get_revision() -> str:
    return context.get_context().get_current_revision()


def get_current_revision() -> str:
    return context.get_context().get_current_revision()


def get_autogenerate() -> bool:
    return context.get_context().get_autogenerate()


def get_dialect() -> object:
    return context.get_context().get_dialect()


def get_connection() -> object:
    return context.get_context().get_connection()


def get_write_connection() -> object:
    return context.get_context().get_write_connection()


def get_read_only_connection() -> object:
    return context.get_context().get_read_only_connection()


def get_drivers() -> dict:
    return context.get_context().get_drivers()


def get_version() -> str:
    return context.get_context().get_version()


def set_version(version: str) -> None:
    context.get_context().set_version(version)


def get_heads() -> list:
    return context.get_context().get_heads()


def get_heads_at_version(version: str) -> list:
    return context.get_context().get_heads_at_version(version)


def get_heads_of_branch(branch: str) -> list:
    return context.get_context().get_heads_of_branch(branch)


def get_head() -> str:
    return context.get_context().get_head()


def get_head_at_version(version: str) -> str:
    return context.get_context().get_head_at_version(version)


def get_head_of_branch(branch: str) -> str:
    return context.get_context().get_head_of_branch(branch)


def get_head_of_branch_at_version(version: str) -> str:
    return context.get_context().get_head_of_branch_at_version(version)


def get_head_of_branch_of_branch(branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch(branch, branch)


def get_head_of_branch_at_version_of_branch(branch: str, version: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_at_version_of_branch(branch, version, branch)


def get_head_of_branch_of_branch_at_version(branch: str, branch: str, version: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version(branch, branch, version)


def get_head_of_branch_of_branch_at_version_of_branch(branch: str, branch: str, version: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch(branch, branch, version, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch(branch, branch, version, branch, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch(branch, branch, version, branch, branch, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch(branch, branch, version, branch, branch, branch, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str, branch: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch(branch, branch, version, branch, branch, branch, branch, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str, branch: str, branch: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch_of_branch(branch, branch, version, branch, branch, branch, branch, branch, branch)


def get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch_of_branch_of_branch_of_branch(branch: str, branch: str, version: str, branch: str, branch: str, branch: str, branch: str, branch: str, branch: str, branch: str) -> str:
    return context.get_context().get_head_of_branch_of_branch_at_version_of_branch_of_branch_of_branch_of_branch_of_branch(branch, branch, version, branch, branch, branch, branch, branch, branch, branch)


def compare_configuration(config: context.Config) -> bool:
    return True


def get_section(name: str) -> dict:
    return config.get_section(config.config_section_name)


def get_revision() -> str:
    return context.get_context().get_current_revision()