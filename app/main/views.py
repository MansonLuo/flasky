from datetime import datetime
from flask import render_template, session, redirect, url_for
from .forms import NameForm
from .. import db, moment
from ..models import User, Role, Permission
from . import main
from flask_login import login_required
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = NameForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.name.data).first():
            #user has exist.
            session['known'] = True

        else:
            #a new user come in
            session['known'] = False
            newUser = User(username=form.name.data, role=Role.query.all()[0])
            db.session.add(newUser)
            db.session.commit()
        session['name'] = form.name.data

        return redirect(url_for('.index'))
    return render_template('index.html', form=form, name=session.get('name'), known=session.get('known', False), current_time=datetime.utcnow())

@main.route('/secret')
@login_required
def secret():
    return 'Only authenticated users are allowed!'

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For administrators!'

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderators_only():
    return "For comment moderators!"
