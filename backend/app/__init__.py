import os
from app.config.environments import config_dict
from flask import Flask
from flask_migrate import Migrate

from .config.pool import init_pool_monitor, check_connection_health
from .extensions import db,cors,mail
# 动态注册蓝图
def register_blueprints(app):
    """自动化注册所有蓝图"""
    from importlib import import_module
    from pathlib import Path

    # 自动发现blueprints目录下的所有蓝图
    blueprints_dir = Path(__file__).parent / "blueprints"
    for bp_dir in blueprints_dir.iterdir():
        if bp_dir.is_dir() and (bp_dir / "__init__.py").exists():
            module = import_module(f"blueprints.{bp_dir.name}")
            if hasattr(module, f"{bp_dir.name}_bp"):
                app.register_blueprint(getattr(module, f"{bp_dir.name}_bp"))
                print(f"Registered blueprint: {bp_dir.name}")

def create_app(config_name=None):
    # 创建Flask实例
    app = Flask(__name__,static_folder='static', static_url_path='/static')

    # 确定配置环境
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'default')

    # 加载配置类
    config_class = config_dict[config_name]
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)
    mail.init_app(app)

    # 配置CORS
    cors.init_app(app,
                  origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
                  methods=['GET', 'POST', 'PUT', 'DELETE','PATCH', 'OPTIONS'],
                  allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
                  supports_credentials=True)

    # 验证数据库URI
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Connection pool config: size={app.config.get('POOL_SIZE')}, max_overflow={app.config.get('MAX_OVERFLOW')}")

    # 注册蓝图
    register_blueprints(app)

    # 初始化连接池监控
    init_pool_monitor(app)

    # 创建数据库表（仅开发环境）
    if app.config.get('ENV') == 'development':
        with app.app_context():
            db.create_all()

        # 测试数据库连接
        with app.app_context():
            health = check_connection_health()
            if health['status'] == 'healthy':
                print("✓ Database connection pool initialized successfully")
            else:
                print(f"✗ Database connection failed: {health.get('message')}")

    if app.debug:
        @app.get('/debug/routes')
        def show_routes():
            from flask import jsonify
            return jsonify({
                'routes': sorted([str(rule) for rule in app.url_map.iter_rules()])
            })

    # 在应用退出时停止清理线程
    # @app.teardown_appcontext
    # def teardown(exception=None):
    #     EmailCaptchaMemoryStorage.stop_cleanup_thread()

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    @app.route('/test-db')
    def test_db_connection():
        """测试数据库连接"""
        try:
            # 使用连接池获取连接
            from sqlalchemy import text
            from .config.pool import get_db_connection, check_connection_health

            # 检查健康状态
            health = check_connection_health()

            # 获取连接池状态
            engine = db.get_engine()
            pool_status = {
                'size': engine.pool.size(),
                'checked_in': engine.pool.checkedin(),
                'checked_out': engine.pool.checkedout(),
                'overflow': engine.pool.overflow()
            }

            return {
                'status': 'success',
                'message': 'Database connection pool is working',
                'health_check': health,
                'pool_status': pool_status,
                'config': {
                    'pool_size': app.config.get('POOL_SIZE'),
                    'max_overflow': app.config.get('MAX_OVERFLOW'),
                    'pool_recycle': app.config.get('POOL_RECYCLE'),
                    'pool_pre_ping': app.config.get('POOL_PRE_PING'),
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database connection failed: {str(e)}'
            }, 500

    # login_before_request(app)

    return app
