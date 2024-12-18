from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db,login
from flask import current_app,url_for
from datetime import datetime,timezone,timedelta
#密码哈希:1.生成哈希密钥 2.检查哈希密钥是否与明文密钥一致两个模块
from werkzeug.security import generate_password_hash, check_password_hash
#Flask-Login 用户 mixin 类
from flask_login import UserMixin, AnonymousUserMixin
#将字符串生成哈希值
from hashlib import md5
import json
from time import time
#jwt令牌生成
import jwt
#支持用户令牌
import secrets

#时区和非时区的时间转化方法
import pytz
utc = pytz.UTC
#MarkDown语法解析
from markdown import markdown
import bleach

from app.search import add_to_index, remove_from_index, query_index
#导入用户任务队列
import redis
import rq

#用户加载器在装饰器的 Flask-Login 中注册
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
'''
生成迁移脚本
flask db migrate -m "new fields in user model"
更改应用与数据库
flask db upgrade
'''
# 追随者关系表，关注者添加到数据库，关联表：followers

'''
数据库更改需要记录在数据库迁移
flask db migrate -m "followers"
 flask db upgrade
'''
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)
# 基本操作混入类
class BaseMixin:
    id = db.Column(db.Integer,primary_key=True)

    @classmethod
    def add(cls,**kwargs):
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def get(cls,id):
        return cls.query.get(id)
        
    def update(self,**kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)
            db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


# 搜索引擎混入类
'''
类中四个函数是类的方法，是与类而不是特定实例特殊关联的方法。
对数据库中当前的所有帖子初始化索引
>>> Post.reindex()
查询五个元素的第一页
query, total = Post.search('世界', 1, 5)
>>> total
18
>>> query.all()
[<Post ..世界..>, <Post 世界...>, <Post 世界....>, <Post 世界...世界>, <Post 世界..>]
'''
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


#分页表示混合类
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page,
                                error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data
        
class Role(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key = True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64),unique = True)
    default: so.Mapped[bool] = so.mapped_column(sa.Boolean(),default = False,index = True)
    permissions: so.Mapped[int] = so.mapped_column(sa.Integer())
    #一对多关系
    users: so.WriteOnlyMapped['User'] = so.relationship(back_populates='role')
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    def add_permission(self,perm):
        if not self.has_permission(perm):
            self.permissions += perm
    def remove_permission(self,perm):
        if self.has_permission(perm):
            self.permissions += perm
    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self,perm):
        return self.permissions & perm == perm
    
    '''
    在shell下执行以下代码，在shell会话添加新角色到数据库中。

    (venv) $ flask shell
    >>> Role.insert_roles()
    >>> Role.query.all()
    [<Role 'Administrator'>, <Role 'User'>, <Role 'Moderator'>]
    '''
    @staticmethod
    def insert_roles():
        roles = {
        'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
        'Moderator': [Permission.FOLLOW, Permission.COMMENT,Permission.WRITE, Permission.MODERATE],
        'Administrator': [Permission.FOLLOW, Permission.COMMENT,
        Permission.WRITE, Permission.MODERATE,
        Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
                role.default = (role.name == default_role)
                db.session.add(role)
        db.session.commit()
    '''
    更新帐户分配用户角色，在shell会话中执行一下代码。
    (venv) $ flask shell
    >> u = User.query.first()
    >> admin_role = Role.query.filter_by(name='Adminstrator').first()
    >> u.role = admin_role
    '''
    @staticmethod
    def get_role():
        admin_role = Role.query.filter_by(name='Administrator').first()
        default_role = Role.query.filter_by(default=True).first()
        for u in User.query.all():
            if u.role is None:
                if u.email == current_app.config['MAIL_USERNAME']:
                    u.role = admin_role
                else:
                    u.role = default_role
        db.session.commit()


#定义权限常量
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

class User(PaginatedAPIMixin,UserMixin,db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,unique=True,nullable = True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140),nullable = True)
    member_since: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc),nullable = True)
    confirmed: so.Mapped[Optional[bool]] = so.mapped_column(sa.Boolean(),default = False,nullable = True)
    #用户任务
    tasks: so.WriteOnlyMapped['Task'] = so.relationship(back_populates='user')
    #用户的评论,user表与comment表之间的一对多关系
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='author')
    #token字段用于构建令牌验证方案
    token: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    '''    
        将tokens失效时间,使用pytz模块utc.localize()将转化为当地时间，.replace(tzinfo=utc)统一转为UTC
        数据库的时间（不含时区）和模块生成的时间（有时区）做比较报错，可以使用pytz模块将数据库的时间转为UTC
        打印出来便知：
        2021-12-30 02:49:04.403354+00:00
        上面是offset-aware型（有时区类型）
        2021-12-30 11:01:33.241246
        上面是offset-native型（不含时区类型）

        处理方法：
        offset-native转为off-aware型：
        datetime.now() -->  datetime.now(timezone.utc)
        offset-aware转为off-native型：
        self.token_expiration.replace(tzinfo=utc) --> self.token_expiration.replace(tzinfo=None)
        '''
    def get_token(self, expires_in=3600):
        now = datetime.now()
      
        token_expiration = self.token_expiration.replace(tzinfo=None)
        if self.token and token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(
            seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
                tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user

    role_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Role.id),index=True,nullable = True)
    role: so.Mapped[Role] = so.relationship(back_populates='users')
    
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc),nullable = True)

    last_message_read_time: so.Mapped[Optional[datetime]]

    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.sender_id', back_populates='author')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.recipient_id', back_populates='recipient')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(
        back_populates='user')
    #一对多关系
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    #关注者多对多
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')

    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MAIL_USERNAME']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        db.session.add(self)
        db.session.commit()
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
        
    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def unread_message_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        query = sa.select(Message).where(Message.recipient == self,
                                         Message.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(
            query.subquery()))
            
    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().where(
            Notification.name == name))
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_confirmed(self):
        self.confirmed = True

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://blog.miguelgrinberg.com/static/images/mega-tutorial/ch06-gravatar-identicon.png'
        #gravatar服务器网站不稳定
        #f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    #把用户设为自己的关注着
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    #添加和删除关注者
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    #他/她关注了我吗
    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None
    
    #关注者列表
    def following_list(self):
        query = self.following.select()
        return db.session.scalars(query).fetchall()

    #关注者列表
    def followers_list(self):
        query = self.followers.select()
        return db.session.scalars(query).fetchall()
        
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)
    # 互关帖子
    def friends_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        Following = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower))
            .join(Author.following.of_type(Following))
            .where(sa.and_(
                Follower.id == self.id,
                Following.id == self.id
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )
    #确认注册用户令牌
    def generate_confirmation_token(self,expires_in = 3600):
        return jwt.encode(
            {'confirm': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    #确认用户
    @staticmethod
    def confirm(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['confirm']
        except:
            return 
        return db.session.get(User, id)
    
    def posts_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.posts.select().subquery())
        return db.session.scalar(query)
    # API返回JSON数据格式
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.replace(
                tzinfo=timezone.utc).isoformat(),
            'about_me': self.about_me,
            'post_count': self.posts_count(),
            'follower_count': self.followers_count(),
            'following_count': self.following_count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'following': url_for('api.get_following', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])


    #重置密码令牌的方法
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)
    #用户任务程序帮助方法
    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue(f'app.tasks.{name}', self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        query = self.tasks.select().where(Task.complete == False)
        return db.session.scalars(query)

    def get_task_in_progress(self, name):
        query = self.tasks.select().where(Task.name == name,
                                          Task.complete == False)
        return db.session.scalar(query)
        
class Post(PaginatedAPIMixin,SearchableMixin,db.Model):
    __tablename__ = 'post'
    __searchable__ = ['body'] #列出可搜索的字段

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.Text(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),index=True)
    body_html: so.Mapped[str] = so.mapped_column(sa.Text(140))
    #帖子下评论,post表与comment表之间的一对多关系
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='post')

    author: so.Mapped[User] = so.relationship(back_populates='posts')
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))
    
    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def comments_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.comments.select().subquery())
        return db.session.scalar(query)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):

        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
        markdown(value, output_format='html'),
        tags=allowed_tags, strip=True))
        db.event.listen(Post.body, 'set', Post.on_changed_body)
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            return None
        return Post(body=body)
    #Api返回JSON格式
    def to_dict(self):
        data = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.user_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments_count()
        }
        return data

class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey(User.id),
                                                 index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                                    index=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))

    author: so.Mapped[User] = so.relationship(
        foreign_keys='Message.sender_id',
        back_populates='messages_sent')
    recipient: so.Mapped[User] = so.relationship(
        foreign_keys='Message.recipient_id',
        back_populates='messages_received')

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key= True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    timestamp: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)
    
    user: so.Mapped[User] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False

login.anonymous_user = AnonymousUser


class Comment(PaginatedAPIMixin,db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key= True)
    body: so.Mapped[str] = so.mapped_column(sa.Text(140),nullable=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc),nullable=True)
    body_html: so.Mapped[str] = so.mapped_column(sa.Text(140),nullable=True)
    
    disabled: so.Mapped[bool] = so.mapped_column(sa.Boolean(True),nullable=True)
    author_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),index=True,nullable=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id),index=True,nullable=True)
    #该评论来自哪个作者或帖子
    author: so.Mapped[User] = so.relationship(back_populates='comments')
    post: so.Mapped[Post] = so.relationship(back_populates='comments')
    

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
        'strong']
        target.body_html = bleach.linkify(bleach.clean(
        markdown(value, output_format='html'),
        tags=allowed_tags, strip=True))
        db.event.listen(Comment.body, 'set', Comment.on_changed_body)

#任务的模型
class Task(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(36), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(128))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))
    complete: so.Mapped[bool] = so.mapped_column(default=False)

    user: so.Mapped[User] = so.relationship(back_populates='tasks')

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
