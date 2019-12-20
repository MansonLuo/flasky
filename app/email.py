from flask_mail import Message
from . import mail
from flask import render_template
from . import create_app


def send_email(to, subject, template, **kwargs):
    app = create_app('default')
    app.config['SERVER_NAME'] = 'example.com'
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
            sender=app.config['FLASKY_MAIL_SENDER'], 
            recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    try:
        with app.app_context():
            mail.send(msg)
    except:
        return False

    return True

    
