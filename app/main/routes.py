from datetime import datetime,timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, PostForm,EmptyForm,MessageForm,CommentForm,EditProfileAdminForm,SearchForm
from app.models import User, Post,Message,Notification,Role,Comment,Permission
#from app.translate import translate
from app.main import bp

import sqlalchemy as sa

#检测语言
from langdetect import detect, LangDetectException

from app.decorators import admin_required, permission_required

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    #g.locale = str(get_locale())
        g.search_form = SearchForm()
    #g.locale = 'zh' if str(get_locale()).startswith('zh') else str(get_locale())
    g.locale = str(get_locale())

@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/explore')
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,pagination = posts,
                           next_url=next_url, prev_url=prev_url,explore=True,index = False)

@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    title = _("Home")
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.body.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.body.data,body_html=form.body.data, author=current_user,language = language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=title, form=form,
                           posts=posts.items, pagination = posts,next_url=next_url,
                           prev_url=prev_url,index = True)

@bp.route('/space')
@login_required
def space():
    title = _("Personal Homepage")
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.body.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.body.data,body_html=form.body.data, author=current_user,language = language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.space'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.friends_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.space', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.space', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("space.html", title=title, posts=posts.items,pagination = posts,
                           next_url=next_url, prev_url=prev_url,space=True)


    
#编辑帖子页面
@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
        not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        post.body_html = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@bp.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You connot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)

@bp.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For administrators!"

@bp.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

#帖子详情页面,支持博客文章评论
@bp.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = db.first_or_404(sa.select(Post).where(Post.id == id))
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
        post=post,
        author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash(_('Your comment has been published.'))
        return redirect(url_for('main.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments_count() - 1) // \
        current_app.config['COMMENTS_PER_PAGE'] + 1
    query = post.comments.select().order_by(Comment.timestamp.desc())
    pagination = db.paginate(query, page=page,
                        per_page=current_app.config['COMMENTS_PER_PAGE'],
                        error_out=False)

    return render_template('post.html', post=post, form=form,
       comments = pagination.items,pagination = pagination)

@bp.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Comment).order_by(Comment.timestamp.desc())
    pagination = db.paginate(query, page=page,
                        per_page=current_app.config['COMMENTS_PER_PAGE'],
                        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
    pagination=pagination, page=page)
    
#评论管理路由
@bp.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = db.first_or_404(sa.select(Comment).where(Comment.id == id))
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate',
        page=request.args.get('page', 1, type=int)))

@bp.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = db.first_or_404(sa.select(Comment).where(Comment.id == id))
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate',
    page=request.args.get('page', 1, type=int)))

#关闭服务器的路由，以便关闭测试服务器
@bp.route('/shutdown')
@permission_required(Permission.MODERATE)
def server_shutdown():
    if not current_app.testing:
        abort(404)
        shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
        shutdown()
    return 'Shutting down...'

'''
@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify(
        {'text': translate(request.form['text'], request.form['source_language'], request.form['dest_language'])})

'''