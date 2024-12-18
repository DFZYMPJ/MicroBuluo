'''
__init__.py将执行并定义包向外界公开的符号。

'''

#工厂模式
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy  # 从包中导入类
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from config import config 
from flask import current_app

#实现异步非阻塞
from gevent import monkey
monkey.patch_all()

#拓展
from flask_pagedown import PageDown
#websocket模块
from flask_socketio import SocketIO
#搜索引擎Elasticsearch
from elasticsearch import Elasticsearch
# Redis集成工程函数中
from redis import Redis
import rq

bootstrap = Bootstrap()

moment = Moment()

babel = Babel()
#提示邮箱对象传入一个参数app，所以初始化app.config[]应在Mail()之前。否则无法发送邮件。

#邮箱对象
mail = Mail()

#管理登录对象
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')

#数据库对象
db = SQLAlchemy()
#迁移引擎对象
migrate = Migrate()

pagedown = PageDown()

#Sockert连接
socketio = SocketIO()


def create_app(config_name = os.getenv('FLASK_CONFIG') or 'default'):

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app,locale_selector=get_locale)
    #初始化Flask—PageDown
    pagedown.init_app(app)
    socketio.init_app(app,async_mode='gevent', ping_timeout = app.config['PING_TIMEOUT'], ping_interval = app.config['PING_INTERVAL'])
    
    '''
        Elasticsearch没有被Flask封装，无法像上例全局范围创建Elasticsearch实例。解决方案就是，调用create_app函数中向实例添加属性。
    '''

    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microbuluo-tasks', connection=app.redis)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    # API蓝图注册
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.gpt import bp as gpt_bp
    app.register_blueprint(gpt_bp, url_prefix='/gpt')

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('MicroBuluo startup')
    return app

#@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

#在app包中导入routes模块,导入新模块models数据库模型,error错误处理
from app import models