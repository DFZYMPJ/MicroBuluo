from app.api import bp

from app.models import Post,Comment,Permission

from app import db

import sqlalchemy as sa

from flask import request,url_for,abort,jsonify

from app.api.errors import bad_request

from app.api.auth import token_auth



'''
http GET http://localhost:5000/api/posts/
'''
#实现各个资源端点GET请求

#获取所有帖子,分页显示
@bp.route('/posts/',methods=['GET'])
@token_auth.login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 100)
    return jsonify(Post.to_collection_dict(sa.select(Post), page, per_page,
                                   'api.get_posts'))

#获取用户的某条帖子
@bp.route('/posts/<int:id>',methods=['GET'])
@token_auth.login_required
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_dict())
    
#获取帖子的所有评论，分页显示
@bp.route('/post/<int:id>/comments',methods=['GET'])
@token_auth.login_required
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    query = post.comments.select().order_by(Comment.timestamp.desc())
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return jsonify(Comment.to_collection_dict(query, page, per_page,
                                   'api.get_post_comments', id=id))

'''
 HTTPie工具接口测试
 http -A bearer --auth <token> POST http://localhost:5000/api/posts "body=少壮不努力，老大写作业！"
'''

#发布新帖子
@bp.route('/posts/', methods=['POST'])
@token_auth.login_required
def new_post():
    data = request.get_json()
    if 'body' not in data:
        return bad_request('must include body fields')
    else:
        post = Post.from_json(request.json)
        post.body = data['body']
        post.body_html = data['body']
        post.author = token_auth.current_user()
        db.session.add(post)
        db.session.commit()
        return jsonify(post.to_dict()), 201, \
            {'Location': url_for('api.get_post', id=post.id)}

    '''
    HTTPie工具接口测试
    http -A bearer --auth <token> PUT http://localhost:5000/api/posts/1 "body=this is a post!"
    '''
# 编辑帖子
@bp.route('/posts/<int:id>', methods=['PUT'])
@token_auth.login_required
def edit_post(id):
    post = db.get_or_404(Post, id)
    if token_auth.current_user().id != post.user_id:
        abort(403)
    data = request.get_json()
    post.body = data['body']
    post.body_html = data['body']
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())

