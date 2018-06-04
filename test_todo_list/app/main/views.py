from flask import render_template, redirect, request, url_for
from flask_login import current_user, login_required
from . import main
from .forms import TodoForm, Todo_listForm
from ..models import Todo, Todo_list


@main.route('/')
def index():
    form = TodoForm()
    if form.validate_on_submit():
        return redirect(url_for('main.new_todo_list'))
    return render_template('index.html', form=form)


@main.route('/todo_lists', methods=['GET', 'POST'])
@login_required
def todo_list_overview():
    form = Todo_listForm()
    if form.validate_on_submit():
        return redirect(url_for('main.add_todo_list'))
    return render_template('overview.html', form=form)


def get_user():
    return current_user.username if current_user.is_authenticated else None


@main.route('/todo_list/<int:id>', methods=['GET', 'POST'])
def todo_list(id):
    todo_list = Todo_list.query.filter_by(id=id).first_or_404()
    form = TodoForm()
    if form.validate_on_submit():
        Todo(form.todo.data, todo_list.id, get_user()).save()
        return redirect(url_for('main.todo_list', id=id))
    return render_template('todo_list.html', todo_list=todo_list, form=form)


@main.route('/todo_list/new', methods=['POST'])
def new_todo_list():
    form = TodoForm(todo=request.form.get('todo'))
    if form.validate():
        todo_list = Todo_list(creator=get_user()).save()
        Todo(form.todo.data, todo_list.id).save()
        return redirect(url_for('main.todo_list', id=todo_list.id))
    return redirect(url_for('main.index'))


@main.route('/todo_list/add', methods=['POST'])
def add_todo_list():
    form = Todo_listForm(todo=request.form.get('title'))
    if form.validate():
        todo_list = Todo_list(form.title.data, get_user()).save()
        return redirect(url_for('main.todo_list', id=todo_list.id))
    return redirect(url_for('main.index'))
