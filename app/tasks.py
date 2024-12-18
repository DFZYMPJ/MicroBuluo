from rq import get_current_job
from app import db,create_app
from app.models import Task,User, Post
import time
import json
from flask import render_template
from app.email import send_email
import sys
import sqlalchemy as sa

app = create_app()
app.app_context().push()

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = db.session.get(Task, job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def export_posts(user_id):
    try:
        user = db.session.get(User, user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = db.session.scalar(sa.select(sa.func.count()).select_from(
            user.posts.select().subquery()))
        for post in db.session.scalars(user.posts.select().order_by(
                Post.timestamp.asc())):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)
        #通过电子邮件向用户发送帖子。
        send_email(
            '[MicroBuluo] Your blog posts',
            sender=app.config['MAIL_USERNAME'], recipients=[user.email],
            text_body=render_template('email/export_posts.txt', user=user),
            html_body=render_template('email/export_posts.html', user=user),
            attachments=[('posts.json', 'application/json',
                          json.dumps({'posts': data}, indent=4))],
            sync=True)
    except Exception:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

'''
运行RQ Worker进程，注意在flask程序目录，如果是在虚拟环境运行flask app，那终端窗口切换到虚拟环境的项目目录下执行命令。
(venv) $ rq worker microbuluo-tasks
8:55:06 RQ worker 'rq:worker:miguelsmac.90369' started, version 0.9.1
18:55:06 Cleaning registries for queue: microbuluo-tasks
18:55:06
18:55:06 *** Listening on microbuluo-tasks...

打开第二个终端窗口，进入python3 shell，执行以下命令。
>>> from redis import Redis
>>> import rq
>>> queue = rq.Queue('microbuluo-tasks', connection=Redis.from_url('redis://'))
>>> job = queue.enqueue('app.tasks.example', 23)
>>> job.get_id()

'c651de7f-21a8-4068-afd5-8b982a6f6d32'
执行23秒后，可以查看job完成进度。

>>> job.is_finished
True

'''

def example(seconds):
    print('Starting task')
    for i in range(seconds):
        print(i)
        time.sleep(1)
    print('Task completed')