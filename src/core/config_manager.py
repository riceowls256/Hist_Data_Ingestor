import yaml
from pathlib import Path
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings

CONFIG_PATH = Path(__file__).parent.parent.parent / 'configs' / 'system_config.yaml'

class DBConfig(BaseSettings):
    user: str
    password: str
    host: str
    port: int
    dbname: str

    class Config:
        env_prefix = 'TIMESCALEDB_'
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    def get_uri(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

class APIConfig(BaseSettings):
    ib_api_key: str
    databento_api_key: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

class LoggingConfig(BaseSettings):
    level: str = 'INFO'
    file: str = 'logs/app.log'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

class SystemConfig(BaseSettings):
    db: DBConfig
    logging: LoggingConfig
    api: APIConfig

    class Config:
        env_nested_delimiter = '__'
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

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
        
        with open(self.config_path, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}

        try:
            # Correctly initialize nested models from the YAML dictionary
            return SystemConfig(
                db=DBConfig(**yaml_config.get('db', {})),
                logging=LoggingConfig(**yaml_config.get('logging', {})),
                api=APIConfig(**yaml_config.get('api', {}))
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
