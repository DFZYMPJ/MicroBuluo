import os
#环境变量设置配置
basedir = os.path.abspath(os.path.dirname(__file__))
'''
我将设置一个唯一且难以猜测的值，以便服务器具有其他人不知道的安全密钥。orSECRET_KEY
'''
#导入.env文件参数
from dotenv import load_dotenv

load_dotenv(os.path.join(basedir, 'microbuluo.env'))

class Config:
    #Flask app配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess2'
    
    '''
    我将从环境变量中获取数据库 URL，如果未定义，我将配置一个名为 app.db 的数据库，该数据库位于应用程序的主目录中，该目录存储在变量中。
    '''
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    #帖子/评论分页数量配置
    POSTS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10

    #Socketio参数配置
    SOCK_SERVER_OPTIONS = os.environ.get('SOCK_SERVER_OPTIONS') or {'ping_interval': 60}
    ENGINEIO_MAX_DECODE_PACKETS = 500
    PING_TIMEOUT = 10
    PING_INTERVAL = 10

    #babel翻译语言类型
    LANGUAGES = ['en', 'zh']

    #邮箱配置
    #使用QQ邮箱
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'flase').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    #客户端授权密码
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # msg = Message('test subject',sender=app.config['MAIL_USERNAME'],recipients=['dfzympj2@foxmail.com'])
    
    #Elasticsearch搜索引擎服务连接配置项
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    #将Redis服务器连接配置项
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    #发送邮件参数
    FLASKY_MAIL_SENDER = 'dfzympj2@foxmail.com'

    FLASKY_ADMIN = 'dfzympj2@foxmail.com'

    FLASKY_MAIL_SUBJECT_PREFIX = '[Microbuluo]'

    @staticmethod
    def init_app(app):
        pass
        
class DevelopeConfig(Config):
    DEBUG = False
    #数据迁移到项目目录中
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

class TestingConfig(Config):
    #禁用CSRF
    WTF_CSRF_ENABLED = False

    TESTING = True
    #数据迁移到项目目录中
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///'

class ProductionConfig(Config):
    DEBUG = False
    #数据迁移到项目目录中
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'application.db')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # 出错时邮件通知管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
        mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
        fromaddr=cls.FLASKY_MAIL_SENDER,
        toaddrs=[cls.FLASKY_ADMIN],
        subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
        credentials=credentials,
        secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

config = {
    'development':DevelopeConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopeConfig
}