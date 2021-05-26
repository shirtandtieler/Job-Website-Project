# Routes are the different URLs that the application implements.
# The functions below handle the routing/behavior.

from flask import render_template, flash, redirect, url_for

from app.main import bp
from app.main.forms import JobPostForm
from flask_login import current_user, login_required
from app.models import SeekerProfile, CompanyProfile, AccountTypes, JobPost


## TODO Routes needed for editing profile page, searching, sending messages, etc.

@bp.route("/")
@bp.route("/index")
def index():
    """ Home page / dashboard for logged in users """
    if current_user.is_anonymous:
        return render_template("index.html", title="Home")

    if current_user.account_type == AccountTypes.s:  # seeker
        prof = current_user._seeker
        _first_name = prof.first_name
        _last_name = prof.last_name
        _name = _first_name + ' ' + _last_name
        _email = current_user.email  # cannot reference prof because seeker doesn't have email attribute
        _phone_number = prof.phone_number
        _city = prof.city
        _state = prof.state
        _resume = prof.resume
        _skills = prof._skills
        _attitudes = prof._attitudes
        _history_edus = prof._history_edus
        _history_jobs = prof._history_jobs
        return render_template("seeker/dashboard.html",
                               fullname=_name, first_name=_first_name, last_name=_last_name,
                               email=_email, phone_number=_phone_number, city=_city, state=_state,
                               resume=_resume, skills=_skills, attitudes=_attitudes,
                               history_edus=_history_edus, history_jobs=_history_jobs)
    elif current_user.account_type == AccountTypes.c:  # company
        profile = current_user._company
        _name = profile.name
        _city = profile.city
        _state = profile.state
        _website = profile.website
        
        return render_template("company/dashboard.html",name=_name, city=_city,state=_state,website=_website)
    else:  # admin
        return render_template("admin/dashboard.html")


@bp.route('/profile')
def profile():
    """
    Displays the user's view of their profile
    """
    # XXX Subject to change soon.
    # Should eventually go to the user's view of their profile. Just goes to the public view for now.
    # (Maybe both will go to the same page but if/else's will show edit buttons or w/e)

    if current_user.is_anonymous:
        flash('Login required for this operation')
        return redirect(url_for('main.login'))

    if current_user.account_type == AccountTypes.s:
        prof = current_user._seeker
        _name = prof.first_name + ' ' + prof.last_name
        return render_template('seeker/profile.html', fullname=_name)
    elif current_user.account_type == AccountTypes.c:
        prof = current_user._company
        _name = prof.name
        if prof.city and prof.state:  # both provided
            _loc = f"{prof.city}, {prof.state}"
        elif prof.city or prof.state:  # one provided
            _loc = prof.city if prof.city else prof.state
        else:  # none provided
            _loc = "USA"
        _url = prof.website
        return render_template('company/profile.html', name=_name, citystate=_loc, url=_url)
    else:  # admins
        return render_template('admin/profile.html')


@bp.route("/postjob", methods=['GET', 'POST'])
@login_required
def postjob():
    """ New job page; non-company users will be redirected to the homepage. """
    if current_user.account_type != AccountTypes.c:
        flash(f'You cannot access this page.')
        return redirect(url_for('main.index'))
    form = JobPostForm()
    if form.validate_on_submit():
        # TODO Add new job post to database
        # TODO redirect to page for newly created job posting
        flash(f'Mock-created job post: {form.title.data}')
        return redirect(url_for('main.index'))
    return render_template('company/newjobpost.html', form=form)


@bp.route("/jobs")
# @login_required
def job_search():
    """
    Navigate to the job search page.
    """
    # TODO limit access to only seekers/admins?

    posts = [(j.job_title, j.company, f"/company/{j.company_id}", j.location, j.expected_salary)
             for j in JobPost.query.all()]
    return render_template('company/browse.html', jobposts=posts)


@bp.route("/job/<jid>", methods=['GET'])
# @login_required
def job_page(jid: int):
    """
    Navigate to the job page with the specified id.
    """
    # TODO limit access?
    post = JobPost.query.filter_by(id=jid).first()
    if post is None:
        flash(f'No job listing with ID #{jid}')
        return redirect(url_for('main.index'))
    return render_template('company/jobpost.html')


@bp.route("/seekers")
# @login_required
def seeker_search():
    """
    Navigate to the seeker search page.
    """
    # TODO should be only for companies/admins?
    seekers = [(s.full_name, s.tag_lines, s.location) for s in SeekerProfile.query.all()]
    return render_template('seeker/browse.html', seekers=seekers)


@bp.route("/seeker/<sid>")
# @login_required
def seeker_profile(seeker_id):
    """
    Navigate to a specific seeker's profile page.
    """
    # TODO limit access?
    prof = SeekerProfile.query.filter_by(id=seeker_id).first()
    if prof is None:
        # could not find profile with that id
        flash(f'No seeker with the id {seeker_id}.')
        return redirect(url_for('main.index'))

    _name = f'{prof.first_name} {prof.last_name}'
    return render_template('seeker/profile.html', fullname=_name)


@bp.route("/company/<company_id>")
def company_profile(company_id: int):
    """
    Navigate to a specific company's profile page.
    """
    prof = CompanyProfile.query.filter_by(id=company_id).first()
    if prof is None:
        # could not find profile with that id
        flash(f'No company with the id {company_id}')
        return redirect(url_for('main.index'))

    _name = prof.name
    if prof.city and prof.state:  # both provided
        _loc = f"{prof.city}, {prof.state}"
    elif prof.city or prof.state:  # one provided
        _loc = prof.city if prof.city else prof.state
    else:  # none provided
        _loc = "USA"
    _url = prof.website

    _job_posts = JobPost.query.filter_by(company_id=company_id).all()

    return render_template('company/profile_public.html', company_name=_name, citystate=_loc, url=_url, job_posts=_job_posts)
