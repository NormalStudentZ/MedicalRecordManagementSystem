from .base import BaseConfig
from .database import DatabaseConfig, ProductionDatabaseConfig
from .email import EmailConfig

class DevelopmentConfig(BaseConfig, DatabaseConfig, EmailConfig):
    DEBUG = True

class TestingConfig(BaseConfig, DatabaseConfig, EmailConfig):
    TESTING = True

class ProductionConfig(BaseConfig, ProductionDatabaseConfig, EmailConfig):
    DEBUG = False
    TESTING = False

config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}