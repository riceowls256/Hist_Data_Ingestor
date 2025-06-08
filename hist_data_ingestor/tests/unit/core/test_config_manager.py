import pytest
from hist_data_ingestor.src.core.config_manager import ConfigManager


def test_config_loads_from_yaml_only(tmp_path, monkeypatch):
    # 1. Create a temporary YAML config file
    config_content = '''
db:
  user: testuser
  password: testpass
  host: localhost
  port: 5432
  dbname: testdb
logging:
  level: INFO
  file: logs/app.log
api:
  ib_api_key: test_ib_key
  databento_api_key: test_db_key
'''
    config_file = tmp_path / "system_config.yaml"
    config_file.write_text(config_content)

    # 2. Ensure no relevant environment variables are set
    monkeypatch.delenv("TIMESCALEDB_USER", raising=False)
    monkeypatch.delenv("TIMESCALEDB_PASSWORD", raising=False)
    monkeypatch.delenv("TIMESCALEDB_HOST", raising=False)
    monkeypatch.delenv("TIMESCALEDB_PORT", raising=False)
    monkeypatch.delenv("TIMESCALEDB_DBNAME", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("IB_API_KEY", raising=False)
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    # 3. Load config using ConfigManager
    cfg = ConfigManager(config_path=config_file).get()

    # 4. Assert values match YAML
    assert cfg.db.user == "testuser"
    assert cfg.db.password == "testpass"
    assert cfg.db.host == "localhost"
    assert cfg.db.port == 5432
    assert cfg.db.dbname == "testdb"
    assert cfg.logging.level == "INFO"
    assert cfg.api.ib_api_key == "test_ib_key"
    assert cfg.api.databento_api_key == "test_db_key"

def test_config_env_var_override(tmp_path, monkeypatch):
    config_content = '''
db:
  user: testuser
  password: testpass
  host: localhost
  port: 5432
  dbname: testdb
logging:
  level: INFO
  file: logs/app.log
api:
  ib_api_key: test_ib_key
  databento_api_key: test_db_key
'''
    config_file = tmp_path / "system_config.yaml"
    config_file.write_text(config_content)

    # Set environment variables to override YAML
    monkeypatch.setenv("TIMESCALEDB_USER", "envuser")
    monkeypatch.setenv("TIMESCALEDB_PASSWORD", "envpass")
    monkeypatch.setenv("TIMESCALEDB_HOST", "envhost")
    monkeypatch.setenv("TIMESCALEDB_PORT", "1234")
    monkeypatch.setenv("TIMESCALEDB_DBNAME", "envdb")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("IB_API_KEY", "env_ib_key")
    monkeypatch.setenv("DATABENTO_API_KEY", "env_db_key")

    cfg = ConfigManager(config_path=config_file).get()
    assert cfg.db.user == "envuser"
    assert cfg.db.password == "envpass"
    assert cfg.db.host == "envhost"
    assert cfg.db.port == 1234
    assert cfg.db.dbname == "envdb"
    assert cfg.logging.level == "DEBUG"
    assert cfg.api.ib_api_key == "env_ib_key"
    assert cfg.api.databento_api_key == "env_db_key"

def test_config_missing_file(tmp_path):
    missing_file = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        ConfigManager(config_path=missing_file)

def test_config_malformed_yaml(tmp_path):
    # Missing required db section
    config_content = '''
logging:
  level: INFO
  file: logs/app.log
api:
  ib_api_key: test_ib_key
  databento_api_key: test_db_key
'''
    config_file = tmp_path / "system_config.yaml"
    config_file.write_text(config_content)
    with pytest.raises(Exception):
        ConfigManager(config_path=config_file)

    # Invalid port type
    config_content2 = '''
db:
  user: testuser
  password: testpass
  host: localhost
  port: not_a_number
  dbname: testdb
logging:
  level: INFO
  file: logs/app.log
api:
  ib_api_key: test_ib_key
  databento_api_key: test_db_key
'''
    config_file2 = tmp_path / "system_config2.yaml"
    config_file2.write_text(config_content2)
    with pytest.raises(Exception):
        ConfigManager(config_path=config_file2) 