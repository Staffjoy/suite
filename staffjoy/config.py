import logging


class DefaultConfig:
    ENV = "prod"
    LOG_LEVEL = logging.INFO
    BASE = "https://www.staffjoy.com/api/v2/"


class StageConfig(DefaultConfig):
    ENV = "stage"
    BASE = "https://stage.staffjoy.com/api/v2/"


class DevelopmentConfig(DefaultConfig):
    ENV = "dev"
    LOG_LEVEL = logging.DEBUG
    BASE = "http://suite.local/api/v2/"

class TestConfig(DefaultConfig):
    ENV = "test"
    LOG_LEVEL = logging.WARNING
    BASE = "http://localhost:8080/api/v2/"

config_from_env = {  # Determined in main.py
    "test": TestConfig,
    "dev": DevelopmentConfig,
    "stage": StageConfig,
    "prod": DefaultConfig,
}
