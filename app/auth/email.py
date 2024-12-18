from flask import render_template, current_app
from flask_babel import _
from app.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(_('[MicroBuluo] Reset Your Password'),
               sender=current_app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def send_verifity_email(user):
    token = user.generate_confirmation_token()
    send_email(_('[MicroBuluo] Confirm Your Account'),
    sender=current_app.config['MAIL_USERNAME'],
    recipients=[user.email],
    text_body=render_template('email/confirm.txt',
                                         user=user, token=token),
    html_body=render_template('email/confirm.html',
                                         user=user, token=token))