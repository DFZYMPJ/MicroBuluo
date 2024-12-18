from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from app import db
from app.models import User, Post
def users(count=5):
    fake = Faker("zh_CN")
    i = 0
    while i < count:
        u = User(email=fake.email(),
        username=fake.name(),
        password_hash='scrypt:32768:8:1$GKFogFEp7iIR5InU$61f6c78e98054b563a2335ef3e96bd39b2440fa710bef496b80cf538d42dfde095faa3aae8b4f45b6475bef8ff3298f0f38f6b5bd9856df3d1b886cc28ea99be',
        confirmed=True,
        #name=fake.user_name(),
        #location=fake.city(),
        about_me=fake.city(),
        member_since=fake.past_date())
        db.session.add(u)
        #try:except IntegrityError:
        db.session.commit()
        i += 1
        
        db.session.rollback()
        
def posts(count=100):
    fake = Faker("zh_CN")
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body=fake.lorem(),
        timestamp=fake.past_date(),
        author=u,body_html=fake.text(),language = 'ch')
        db.session.add(p)
        db.session.commit()
        