import yaml
from pathlib import Path
from pydantic import Field, ValidationError, ConfigDict
from pydantic_settings import BaseSettings

CONFIG_PATH = Path(__file__).parent.parent.parent / 'configs' / 'system_config.yaml'


class DBConfig(BaseSettings):
    model_config = ConfigDict(
        env_prefix='TIMESCALEDB_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    user: str
    password: str
    host: str
    port: int
    dbname: str

    def get_uri(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


class APIConfig(BaseSettings):
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    ib_api_key: str
    databento_api_key: str


class LoggingConfig(BaseSettings):
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    level: str = 'DEBUG'        # File logging level (comprehensive)
    console_level: str = 'WARNING'  # Console logging level (user-facing only)
    file: str = 'logs/app.log'


class SystemConfig(BaseSettings):
    model_config = ConfigDict(
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    db: DBConfig
    logging: LoggingConfig
    api: APIConfig


class ConfigManager:
    """
    Loads system configuration by layering sources:
    1. Default values in Pydantic models.
    2. Values from system_config.yaml.
    3. Values from environment variables (or .env file).
    Pydantic handles the priority automatically.
    """

    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        # Verify config file exists and is readable
        with open(self.config_path, 'r') as f:
            yaml.safe_load(f)  # Validate YAML syntax

        try:
            # Initialize each config independently to avoid cross-contamination
            db_config = DBConfig()  # This will load from env with TIMESCALEDB_ prefix
            logging_config = LoggingConfig()  # This will load from env
            api_config = APIConfig()  # This will load from env

            # Create the system config with pre-initialized nested configs
            return SystemConfig(
                db=db_config,
                logging=logging_config,
                api=api_config
            )
        except ValidationError as e:
            raise ValueError(f"Config validation error: {e}")

    def get(self):
        return self.config


# Example usage
if __name__ == "__main__":
    from utils.custom_logger import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
    cfg = ConfigManager().get()
    logger.info(cfg.dict())
