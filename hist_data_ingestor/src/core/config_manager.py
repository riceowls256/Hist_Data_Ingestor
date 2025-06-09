from pathlib import Path
import yaml
from pydantic import BaseSettings, Field, ValidationError

CONFIG_PATH = Path(__file__).parent.parent.parent / 'configs' / 'system_config.yaml'

class DBConfig(BaseSettings):
    user: str = Field(..., env='TIMESCALEDB_USER')
    password: str = Field(..., env='TIMESCALEDB_PASSWORD')
    host: str = Field('localhost', env='TIMESCALEDB_HOST')
    port: int = Field(5432, env='TIMESCALEDB_PORT')
    dbname: str = Field('hist_data_ingestor', env='TIMESCALEDB_DBNAME')

    class Config:
        env_prefix = ''
        case_sensitive = False

class LoggingConfig(BaseSettings):
    level: str = Field('INFO', env='LOG_LEVEL')
    file: str = Field('logs/app.log')

    class Config:
        env_prefix = ''
        case_sensitive = False

class APIConfig(BaseSettings):
    ib_api_key: str = Field(..., env='IB_API_KEY')
    databento_api_key: str = Field(..., env='DATABENTO_API_KEY')

    class Config:
        env_prefix = ''
        case_sensitive = False

class SystemConfig(BaseSettings):
    db: DBConfig
    logging: LoggingConfig
    api: APIConfig

    class Config:
        env_nested_delimiter = '__'
        case_sensitive = False

class ConfigManager:
    """
    Loads system configuration from YAML file, with environment variables automatically overriding defaults via Pydantic BaseSettings.
    """
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            raw = yaml.safe_load(f)
        try:
            return SystemConfig(**raw)
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
