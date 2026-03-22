from logging.config import fileConfig
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_online():
    pass

run_migrations_online()