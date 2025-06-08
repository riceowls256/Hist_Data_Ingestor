from pathlib import Path
import os
import yaml
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent.parent / 'configs' / 'system_config.yaml'

class DBConfig(BaseModel):
    user: str
    password: str
    host: str
    port: int
    dbname: str

class LoggingConfig(BaseModel):
    level: str = 'INFO'
    file: str = 'logs/app.log'

class APIConfig(BaseModel):
    ib_api_key: str
    databento_api_key: str

class SystemConfig(BaseModel):
    db: DBConfig
    logging: LoggingConfig
    api: APIConfig

class ConfigManager:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            raw = yaml.safe_load(f)
        # Override with environment variables if present
        raw['db']['user'] = os.getenv('TIMESCALEDB_USER', raw['db'].get('user', ''))
        raw['db']['password'] = os.getenv('TIMESCALEDB_PASSWORD', raw['db'].get('password', ''))
        raw['db']['host'] = os.getenv('TIMESCALEDB_HOST', raw['db'].get('host', 'localhost'))
        # Robustly handle port override and placeholder values
        port_env = os.getenv('TIMESCALEDB_PORT')
        port_yaml = raw['db'].get('port', 5432)
        try:
            if port_env is not None:
                raw['db']['port'] = int(port_env)
            else:
                # If the YAML value is a string (e.g., a placeholder), try to convert
                if isinstance(port_yaml, int):
                    raw['db']['port'] = port_yaml
                elif isinstance(port_yaml, str):
                    if port_yaml.isdigit():
                        raw['db']['port'] = int(port_yaml)
                    else:
                        raise ValueError(f"Invalid port value in config: '{port_yaml}'. Must be an integer or a valid environment variable.")
                else:
                    raise ValueError(f"Invalid port value type in config: {type(port_yaml)}. Must be int or str.")
        except Exception as e:
            raise ValueError(f"Error parsing TIMESCALEDB_PORT: {e}")
        raw['db']['dbname'] = os.getenv('TIMESCALEDB_DBNAME', raw['db'].get('dbname', 'hist_data_ingestor'))
        raw['logging']['level'] = os.getenv('LOG_LEVEL', raw['logging'].get('level', 'INFO'))
        raw['api']['ib_api_key'] = os.getenv('IB_API_KEY', raw['api'].get('ib_api_key', ''))
        raw['api']['databento_api_key'] = os.getenv('DATABENTO_API_KEY', raw['api'].get('databento_api_key', ''))
        try:
            return SystemConfig(**raw)
        except ValidationError as e:
            raise ValueError(f"Config validation error: {e}")

    def get(self):
        return self.config

# Example usage
if __name__ == "__main__":
    cfg = ConfigManager().get()
    print(cfg.dict())
