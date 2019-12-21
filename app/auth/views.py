from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ResetPasswordForm, ChangeEmailForm

from flask_login import logout_user, login_required, current_user
from .. import db
from ..email import send_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')

    return redirect(url_for('main.index'))

@auth.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)

        flash('A confirmation email has been sent to you by email.')

        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)
    

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    
    return redirect(url_for('main.index'))


#requre user to comfirm account as quickly as you can through html page
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
            current_user.ping()
            if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
                
                return redirect(url_for('auth.unconfirmed'))
                

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')

    return redirect(url_for('main.index'))

@auth.route('/change_password', methods=['POST', 'GET'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            u = User.query.filter_by(username=current_user.username).first()
            u.password = form.new_password.data
            db.session.add(u)
            db.session.commit()

            flash('You have altered your password successfully.')
            
            logout_user()
            return redirect(url_for('main.index'))
        else:
            flash('Old Password mismatch.')
            return render_template('auth/change-password.html', form=form)
    return render_template('auth/change-password.html', form=form)

@auth.route('/reset_password')
@login_required
def reset_password():
    #generate token
    token = current_user.generate_confirmation_token()

    #send confirmation email
    send_email(current_user.email, 'test', 'auth/email/reset_password', token=token)
    #dispatch control to other route function to deal with confirm token and display form, as well change password

    return redirect(url_for('main.index'))


@auth.route('/confirm-of-reset-password/<token>', methods=['POST', 'GET'])
def confirm_of_reset_password(token):
    form = ResetPasswordForm()

    if form.validate_on_submit():
        s = Serializer(current_app.config['SECRET_KEY'])
        user_id = s.loads(token)['confirm']
        
        u = User.query.get(user_id)
        if u:
            u.password = form.new_password.data
            db.session.add(u)
            db.session.commit()
        else:
            print('error')
        return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/change-email')
@login_required
def change_email():
    token = current_user.generate_confirmation_token()

    send_email(current_user.email, 'test', 'auth/email/change_email', user=current_user, token=token)
    
    return redirect(url_for('main.index'))

@auth.route('/confirm-of-change-email/<token>', methods=['POST', 'GET'])
@login_required
def confirm_of_change_email(token):
    form = ChangeEmailForm()

    if form.validate_on_submit():
        u = User.query.filter_by(username=current_user.username).first()
        u.new_email = form.new_email.data
        u.confirmed = False
        db.session.add(u)
        db.session.commit()

        send_email(current_user.new_email, 'test', 'auth/email/confirm', token=current_user.generate_confirmation_token())
        flash('Your email has changed, please confirm your new Email right now.')

        return redirect(url_for('main.index'))

    return render_template('auth/change-email.html', form=form)
