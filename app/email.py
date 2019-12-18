from flask_mail import Message
from . import mail
from flask import render_template
from . import create_app

app = create_app('default')

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
            sender=app.config['FLASKY_MAIL_SENDER'], 
            recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    try:
        mail.send(msg)
    except:
        return False

    return True

    
