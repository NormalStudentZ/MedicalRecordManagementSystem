import time
import logging
from contextlib import contextmanager
from flask import current_app
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db

logger = logging.getLogger(__name__)


class ConnectionPoolMonitor:
    """数据库连接池监控器"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.extensions['pool_monitor'] = self

        # 注册监控端点（仅在调试模式）
        if app.debug or app.config.get('ENABLE_POOL_MONITOR', False):
            self._register_routes(app)

        # 在应用上下文中设置事件监听器
        with app.app_context():
            self._setup_engine_events(app)

    def _setup_engine_events(self, app):
        """设置数据库引擎事件监听器"""
        try:
            engine = db.get_engine()

            # 移除可能已存在的监听器
            event.remove(engine, 'connect', self.on_connect)
            event.remove(engine, 'checkout', self.on_checkout)
            event.remove(engine, 'checkin', self.on_checkin)
        except:
            pass  # 如果监听器不存在，忽略错误

        # 添加事件监听器
        @event.listens_for(engine, 'connect')
        def on_connect(dbapi_connection, connection_record):
            """连接建立时触发"""
            logger.debug(
                f"New database connection established. Pool size: {connection_record.info.get('pool_size', 'N/A')}")
            # 设置连接编码
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("SET client_encoding TO 'UTF8'")
                cursor.close()
            except:
                pass

        @event.listens_for(engine, 'checkout')
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """从连接池取出连接时触发"""
            if app.debug:
                logger.debug(f"Connection checked out. Active connections: {engine.pool.checkedout()}")

        @event.listens_for(engine, 'checkin')
        def on_checkin(dbapi_connection, connection_record):
            """连接返回连接池时触发"""
            if app.debug:
                logger.debug(f"Connection checked in. Available connections: {engine.pool.checkedin()}")

    def _register_routes(self, app):
        """注册连接池监控路由"""

        @app.get('/debug/pool-status')
        def pool_status():
            """查看连接池状态"""
            from flask import jsonify

            try:
                with app.app_context():
                    engine = db.get_engine()
                    pool = engine.pool

                    status = {
                        'size': pool.size(),
                        'checked_in': pool.checkedin(),
                        'checked_out': pool.checkedout(),
                        'overflow': pool.overflow(),
                        'pool_class': pool.__class__.__name__,
                    }

                    return jsonify({
                        'status': 'success',
                        'pool_status': status,
                        'config': {
                            'pool_size': app.config.get('POOL_SIZE'),
                            'max_overflow': app.config.get('MAX_OVERFLOW'),
                            'pool_recycle': app.config.get('POOL_RECYCLE'),
                            'pool_pre_ping': app.config.get('POOL_PRE_PING'),
                        }
                    })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        @app.get('/debug/test-pool-performance')
        def test_pool_performance():
            """测试连接池性能"""
            from flask import jsonify, request

            n = request.args.get('count', default=10, type=int)

            start_time = time.time()
            results = []

            try:
                with app.app_context():
                    for i in range(n):
                        conn_start = time.time()
                        with db.engine.connect() as conn:
                            conn.execute(text('SELECT 1'))
                            conn_end = time.time()
                            results.append(conn_end - conn_start)

                    total_time = time.time() - start_time

                    return jsonify({
                        'status': 'success',
                        'total_queries': n,
                        'total_time': round(total_time, 4),
                        'avg_time': round(total_time / n, 4),
                        'min_time': round(min(results), 4) if results else 0,
                        'max_time': round(max(results), 4) if results else 0,
                        'pool_status': {
                            'size': db.engine.pool.size(),
                            'checked_in': db.engine.pool.checkedin(),
                            'checked_out': db.engine.pool.checkedout(),
                            'overflow': db.engine.pool.overflow(),
                        }
                    })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器

    使用示例:
        with get_db_connection() as conn:
            result = conn.execute(text('SELECT * FROM users'))
    """
    conn = None
    try:
        # 确保在应用上下文中
        if current_app:
            conn = db.engine.connect()
        else:
            # 如果没有应用上下文，使用默认引擎
            from flask import Flask
            app = Flask(__name__)
            with app.app_context():
                conn = db.engine.connect()
        yield conn
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器

    使用示例:
        with get_db_session() as session:
            user = session.query(User).first()
    """
    session = db.session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def check_connection_health():
    """检查数据库连接健康状况"""
    try:
        # 确保在应用上下文中
        if current_app:
            with db.engine.connect() as conn:
                result = conn.execute(text('SELECT 1'))
                return {
                    'status': 'healthy',
                    'message': 'Database connection is working',
                    'result': result.scalar() == 1
                }
        else:
            # 如果没有应用上下文，尝试创建临时上下文
            from flask import Flask
            app = Flask(__name__)
            with app.app_context():
                with db.engine.connect() as conn:
                    result = conn.execute(text('SELECT 1'))
                    return {
                        'status': 'healthy',
                        'message': 'Database connection is working',
                        'result': result.scalar() == 1
                    }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}',
            'error': str(e)
        }


# 初始化函数
def init_pool_monitor(app):
    """初始化连接池监控"""
    monitor = ConnectionPoolMonitor(app)
    return monitor