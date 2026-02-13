import os

class EmailConfig:
    """邮箱配置"""
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = os.getenv('MAIL_PORT', 465)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', False)
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '3439458467@qq.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'zznlilfnjucrdbhh')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '3439458467@qq.com')