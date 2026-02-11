import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_dev_secret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 数据库配置（直接生成URI字符串）
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'hhh114514')
    DB_NAME = os.getenv('DB_NAME', 'CaseManagementSystem')

    #邮箱配置
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = os.getenv('MAIL_PORT', 465)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', False).lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', True).lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '3439458467@qq.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'zznlilfnjucrdbhh')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '3439458467@qq.com')


    # 直接定义为类属性（而不是property）
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=UTF8"

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    # 生产环境强制检查环境变量
    DB_HOST = os.getenv('PROD_DB_HOST')
    DB_USER = os.getenv('PROD_DB_USER')
    DB_PASSWORD = os.getenv('PROD_DB_PASSWORD')
    DB_NAME = os.getenv('PROD_DB_NAME')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if None in [self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]:
            raise ValueError("Missing required production DB configuration")
        return super().SQLALCHEMY_DATABASE_URI


config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}