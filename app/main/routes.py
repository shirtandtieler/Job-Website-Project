# Routes are the different URLs that the application implements.
# The functions below handle the routing/behavior.

from flask import render_template, flash, redirect, url_for, request

import app
from app import constants
from app.api.jobpost import new_jobpost, extract_details, edit_jobpost
from app.main import bp
from app.main.forms import JobPostForm, SkillRequirementForm, AttitudeRequirementForm
from flask_login import current_user, login_required
from app.models import SeekerProfile, CompanyProfile, AccountTypes, JobPost, Skill, Attitude

## TODO Routes needed for editing profile page, searching, sending messages, etc.
from resources.generators import ATTITUDE_NAMES, SKILL_NAMES


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

        return render_template("company/dashboard.html", name=_name, city=_city, state=_state, website=_website)
    else:  # admin
        return render_template("admin/dashboard.html")


@bp.route('/profile')
def profile():
    """
    Displays the user's own profile (the same as the public view, but with some extra logic)
    """

    if current_user.is_anonymous:
        flash('Login required for this operation')
        return redirect(url_for('main.login'))

    if current_user.account_type == AccountTypes.s:
        # Show seeker's public profile page
        return seeker_profile(current_user._seeker.id)
    elif current_user.account_type == AccountTypes.c:
        # Show company's public profile page
        return company_profile(current_user._company.id)
    else:  # admins
        return render_template('admin/profile.html')


@bp.route("/seeker/<seeker_id>")
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

    _job_posts = JobPost.query.filter_by(company_id=company_id).order_by(JobPost.created_timestamp).all()

    return render_template('company/profile.html', company_name=_name, citystate=_loc, url=_url,
                           job_posts=_job_posts)


@bp.route("/job/new", methods=['GET', 'POST'])
@login_required
def new_job():
    """ New job page; non-company users will be redirected to the homepage. """
    if current_user.account_type != AccountTypes.c:
        flash(f'You cannot access this page.')
        return redirect(url_for('main.index'))
    form = JobPostForm()
    if form.validate_on_submit():
        deets = extract_details(form)
        post_id = new_jobpost(current_user._company.id, deets.pop('title'), **deets)
        flash(f"Created job post with ID {post_id}")
        return redirect(url_for('main.job_page', job_id=post_id))
    return render_template('company/jobpost_editor.html',
                           form=form, skill_list=SKILL_NAMES, attitude_list=ATTITUDE_NAMES
                           )


@bp.route("/job/edit/<job_id>", methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job_post = JobPost.query.filter_by(id=job_id).first_or_404()

    # Don't allow to editor if user isn't a company or if the post doesn't belong to the company.
    if current_user.account_type != AccountTypes.c or job_post.company_id != current_user._company.id:
        flash(f'You cannot access this page.')
        return redirect(url_for('main.index'))

    form = JobPostForm()
    if form.validate_on_submit():  # using POST; push changes
        deets = extract_details(form)
        edit_jobpost(job_id, **deets)
        flash(f"Edited job successfully.")
        return redirect(url_for('main.job_page', job_id=job_id))

    # using GET; fill out form with current job post information
    form.title.data = job_post.job_title
    form.city.data = job_post.city
    form.state.data = job_post.state
    form.description.data = job_post.description
    form.remote.data = job_post.is_remote
    form.salary_min.data = job_post.salary_min
    form.salary_max.data = job_post.salary_max
    form.active.data = job_post.active
    # skills/attitudes need to be passed as arguments
    _skls = [[s._skill.title, int(s.skill_level_min), int(s.importance_level)] for s in job_post._skills]
    _atts = [[a._attitude.title, int(a.importance_level)] for a in job_post._attitudes]
    return render_template('company/jobpost_editor.html',
                           form=form, skill_list=SKILL_NAMES, attitude_list=ATTITUDE_NAMES,
                           init_skills=_skls, init_attitudes=_atts
                           )


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


@bp.route("/job/<job_id>")
# @login_required
def job_page(job_id: int):
    """
    Navigate to the job page with the specified id.
    """
    # TODO limit access?
    job_post = JobPost.query.filter_by(id=job_id).first_or_404()
    return render_template('company/jobpost.html', job=job_post)


@bp.route("/seekers")
# @login_required
def seeker_search():
    """
    Navigate to the seeker search page.
    """
    # TODO should be only for companies/admins?
    # `request` is a global value that lets you check the URL request.
    page = request.args.get('page', 1, type=int)

    # query.all can be replaced with query.paginate to iteratively get that page's results.
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#flask_sqlalchemy.BaseQuery.paginate
    pager = SeekerProfile.query.paginate(
        page, app.Config.RESULTS_PER_PAGE, False)

    prev_url = url_for('main.seeker_search', page=pager.prev_num) if pager.has_prev else "#"
    prev_link_clz = "disabled" if not pager.has_prev else ""

    next_url = url_for('main.seeker_search', page=pager.next_num) if pager.has_next else "#"
    next_link_clz = "disabled" if not pager.has_next else ""

    # get lower and upper page count for up to 5 surrounding pages
    max_window = min(5, pager.pages)
    pg_lower = pg_upper = page
    while pg_upper-pg_lower+1 < max_window:
        pg_lower = max(1, pg_lower-1)
        pg_upper = min(pager.pages, pg_upper+1)

    return render_template('seeker/browse.html',
                           seeker_profiles=pager.items,  # .items gets the list of profiles
                           page=page,
                           plwr=pg_lower, pupr=pg_upper,
                           dprev=prev_link_clz, prev_url=prev_url,
                           dnext=next_link_clz, next_url=next_url,
                           )
