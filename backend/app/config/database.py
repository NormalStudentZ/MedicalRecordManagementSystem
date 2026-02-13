import os
from urllib.parse import quote_plus

class DatabaseConfig:
    """数据库配置"""
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', 'hhh114514'))
    DB_NAME = os.getenv('DB_NAME', 'CaseManagementSystem')

    # 连接池配置
    POOL_SIZE = int(os.getenv('POOL_SIZE', '10'))
    MAX_OVERFLOW = int(os.getenv('MAX_OVERFLOW', '20'))
    POOL_RECYCLE = int(os.getenv('POOL_RECYCLE', '3600'))
    POOL_PRE_PING = os.getenv('POOL_PRE_PING', 'True').lower() == 'true'
    POOL_TIMEOUT = int(os.getenv('POOL_TIMEOUT', '30'))

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=UTF8"

    # SQLAlchemy引擎配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': POOL_SIZE,  # 连接池大小
        'max_overflow': MAX_OVERFLOW,  # 最大溢出连接数
        'pool_recycle': POOL_RECYCLE,  # 连接回收时间
        'pool_pre_ping': POOL_PRE_PING,  # 连接前检查
        'pool_timeout': POOL_TIMEOUT,  # 获取连接超时时间
        'echo_pool': os.getenv('ECHO_POOL', 'False').lower() == 'true',  # 连接池日志
        'pool_reset_on_return': 'rollback',  # 连接返回池时的回滚策略
    }

class ProductionDatabaseConfig(DatabaseConfig):
    """生产环境数据库配置"""
    DB_HOST = os.getenv('PROD_DB_HOST')
    DB_USER = os.getenv('PROD_DB_USER')
    DB_PASSWORD = os.getenv('PROD_DB_PASSWORD')
    DB_NAME = os.getenv('PROD_DB_NAME')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if None in [self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]:
            raise ValueError("Missing required production DB configuration")
        return super().SQLALCHEMY_DATABASE_URI