from flask import url_for, flash, render_template
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.utils import redirect

from app.api.users import new_seeker, new_company, update_last_login
from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """ Handles the login page by showing and submitting the form """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        update_last_login(user.id)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """ Handles the registration page by showing and submitting the form """
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            flash(f'User {form.email.data} is already registered!')
            return redirect(url_for('auth.login'))
        # create new user and add to the database
        if form.account_type.data.lower().startswith("s"):
            new_func = new_seeker
        else:
            new_func = new_company
        new_func(form.email.data, form.password.data)
        # atype = AccountTypes.s if form.account_type.data.lower().startswith("s") else AccountTypes.c
        # user = User(account_type = atype, email = form.email.data)
        # user.set_password(form.password.data)  # hashes it
        # db.session.add(user)
        #
        # db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('register.html', title='Register', form=form)
