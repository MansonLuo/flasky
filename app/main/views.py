from datetime import datetime
from flask import render_template, session, redirect, url_for
from .forms import NameForm
from .. import db, moment
from ..models import User, Role
from . import main


@main.route('/', methods=['GET', 'POST'])
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
