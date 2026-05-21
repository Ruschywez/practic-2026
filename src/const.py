from pathlib import Path

CORE_PATH = Path(__file__).resolve().parent.parent
DB_PATH = CORE_PATH / 'database.db'
ENV_PATH = CORE_PATH / '.env'
CONTAINER_PATH = CORE_PATH / 'container'

DB_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"
EXPIRATION_TIME = 30 # days
CHUNK_SIZE = 1024 * 1024