import json
import sys

from wtforms.fields.html5 import IntegerRangeField

from WebAppOptimizer.app.main.utils import *

from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, session
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from WebAppOptimizer.app import db
from WebAppOptimizer.app.main.forms import EditProfileForm, EmptyForm, ConfigurationForm, GetFromLibraForm, OptimizationForm, BodyForm
from WebAppOptimizer.app.models import User, Post, Configuration
from WebAppOptimizer.app.main import bp
import requests


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title=_('Home'), user=current_user)


##########################   FIRST STEP   ##################################

@bp.route('/webapp/first_step', methods=['GET', 'POST'])
@login_required
def first_step():
    form = ConfigurationForm()

    response = requests.get('http://0.0.0.0:4996/api/get_plants')
    session['plants_data'] = response.json()
    if request.method == 'POST':
        return redirect(url_for('main.save_config', form=form))
    else:
        return render_template('step1.html', title=_('Step 1'), form=form)


@bp.route('/config/save', methods=['POST'])
@login_required
def save_config():
    form = ConfigurationForm(request.form)
    if not form.remember_conf.data:
        conf = Configuration(confname='Unknown',
                             body=subdict(form.body.data, [i['name'] for i in session['plants_data']['data']]),
                             datetime=form.date.data, user=current_user,
                             timestamp=datetime.utcnow())
    else:
        conf = Configuration(confname=form.confname.data,
                             body=subdict(form.body.data, [i['name'] for i in session['plants_data']['data']]),
                             datetime=form.date.data, user=current_user,
                             timestamp=datetime.utcnow())
        db.session.add(conf)
        db.session.commit()

    selelectedconfig = get_selected_config(conf, session['plants_data']['data'])
    session.clear()
    session['config_data'] = json.dumps(selelectedconfig)
    session['rendering_data'] = json.dumps("")

    flash('Configuration successfully set.')

    prev_url = url_for('main.first_step')

    return redirect(url_for('main.second_step', prev_url=prev_url))


##########################   SECOND STEP   ##################################

@bp.route('/webapp/second_step', methods=['GET', 'POST'])
@login_required
def second_step():
    if request.method == 'POST':
        form = GetFromLibraForm()
        profiles_data = session['profiles_data']

        render_get_from_libra(form, profiles_data)

        prev_url = url_for('main.first_step')
        next_url = url_for('main.third_step')

        return render_template('step2.html', title=_('Step 2'), form=form, prev_url=prev_url, next_url=next_url)
    else:
        form = GetFromLibraForm()
        prev_url = url_for('main.first_step')

        form.table_title = {'disabled': True}

        return render_template('step2.html', title=_('Step 2'), form=form, prev_url=prev_url)


@bp.route('/aggregator/get_baselines', methods=['POST'])
@login_required
def get_baselines():
    configuration = session['config_data']
    response = requests.get('http://0.0.0.0:4996/api/get_baselines', json=configuration)

    profiles = create_profiles(response.json())
    session['profiles_data'] = profiles

    return redirect(url_for('main.second_step'), code=307)


##########################   THIRD STEP   ##################################

@bp.route('/webapp/third_step', methods=['GET', 'POST'])
@login_required
def third_step():
    form = OptimizationForm()
    if request.method == 'POST':
        prev_url = url_for('main.second_step')

        if "submit1" in request.form:
            to_optimize = session['profiles_data']
            response = requests.post('http://0.0.0.0:4996/api/local_optimization', json=to_optimize)
            result = response.json()

            render_opt_result_table(form, result)

            form.submit2.render_kw = {'disabled': False}

            session['local_opt_result_data'] = result

            return render_template('step3.html', title=_('Step 3'), form=form, prev_url=prev_url)

        if "submit2" in request.form:
            to_aggregate = session['local_opt_result_data']
            # print(to_aggregate)
            print(form.table_title.data)
            response = requests.post('http://0.0.0.0:4996/api/aggregate', json=json.dumps(to_aggregate))
            result = response.json()

            image1, image2, image3 = plot_results(result)
            return render_template('step3.html', title=_('Step 3'), form=form, images=[image1, image2, image3],
                                   prev_url=prev_url)

    else:
        form.table_title = {'disabled': True}
        form.submit2.render_kw = {'disabled': True}
        prev_url = url_for('main.second_step')
        return render_template('step3.html', title=_('Step 3'), form=form, prev_url=prev_url)


@bp.route('/aggregator/run_first_optimization', methods=['GET', 'POST'])
@login_required
def run_first_optimization():
    to_optimize = session['profiles_data']

    response = requests.post('http://0.0.0.0:4996/api/local_optimization', json=to_optimize)
    result = response.json()
    session['first_optimization_data'] = result

    return redirect(url_for('main.third_step'), code=307)


@bp.route('/aggregator/run_second_optimization', methods=['GET', 'POST'])
@login_required
def run_second_optimization():
    to_optimize = session['profiles_data']

    response = requests.post('http://0.0.0.0:4996/api/optimize_and_aggregate', json=to_optimize)
    result = response.json()

    session['second_optimization_data'] = result
    return redirect(url_for('main.third_step'), code=307)


##########################   PROFILE   ##################################
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    configurations = user.configurations.order_by(Configuration.timestamp.desc()).paginate(
        page, current_app.config['CONFS_PER_PAGE'], False)
    # next_url = url_for('main.user', username=user.username,
    #                   page=configuration.next_num) if configuration.has_next else None
    # prev_url = url_for('main.user', username=user.username,
    #                   page=configuration.prev_num) if configuration.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, configurations=configurations.items,
                           form=form)


@bp.route('/config/delete/<int:conf_id>', methods=['POST'])
@login_required
def delete_config(conf_id):
    conf = Configuration.query.get_or_404(conf_id)
    db.session.delete(conf)
    db.session.commit()
    flash(_('Item deleted.'))
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
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
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)

# @bp.route('/translate', methods=['POST'])
# @login_required
# def translate_text():
#    return jsonify({'text': translate(request.form['text'],
#                                      request.form['source_language'],
#                                      request.form['dest_language'])})
