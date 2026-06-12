import csv
import json
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import current_user, login_required
from sqlalchemy import or_, case
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Task, Tag, Activity
from app.forms import TaskForm

tasks_bp = Blueprint('tasks', __name__)

def log_activity(user_id, action, entity_type=None, entity_id=None):
    """Helper to log system activities."""
    activity = Activity(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id)
    db.session.add(activity)

def process_tags(task, tags_string):
    """Helper to convert comma separated string to Tag objects."""
    task.tags.clear()
    if not tags_string:
        return
    tag_names = [t.strip() for t in tags_string.split(',') if t.strip()]
    for name in set(tag_names):
        tag = Tag.query.filter_by(name=name, user_id=current_user.id).first()
        if not tag:
            tag = Tag(name=name, user_id=current_user.id)
            db.session.add(tag)
        task.tags.append(tag)


@tasks_bp.route('/tasks')
@login_required
def list_tasks():
    """List all tasks belonging to the current user with advanced filtering, sorting, and pagination."""
    # N+1 query optimization using joinedload for tags
    query = current_user.tasks.filter_by(is_deleted=False).options(joinedload(Task.tags))

    search_query = request.args.get('q', '').strip()
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_filter),
                Task.description.ilike(search_filter),
                Task.category.ilike(search_filter),
                Task.tags.any(Tag.name.ilike(search_filter))
            )
        )

    status_filter = request.args.get('status')
    if status_filter in ['Pending', 'In Progress', 'Completed']:
        query = query.filter(Task.status == status_filter)

    priority_filter = request.args.get('priority')
    if priority_filter in ['Low', 'Medium', 'High']:
        query = query.filter(Task.priority == priority_filter)

    due_date_filter = request.args.get('due_date')
    today_date = date.today()
    if due_date_filter == 'Today':
        query = query.filter(Task.due_date == today_date)
    elif due_date_filter == 'Upcoming':
        query = query.filter(Task.due_date > today_date)
    elif due_date_filter == 'Overdue':
        query = query.filter(Task.due_date < today_date, Task.status != 'Completed')

    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')

    priority_order = case(
        (Task.priority == 'High', 3),
        (Task.priority == 'Medium', 2),
        (Task.priority == 'Low', 1),
        else_=0
    )

    sort_column = Task.created_at
    if sort_by == 'due_date':
        sort_column = Task.due_date
    elif sort_by == 'updated_at':
        sort_column = Task.updated_at
    elif sort_by == 'priority':
        sort_column = priority_order
    elif sort_by == 'title':
        sort_column = Task.title

    if sort_dir == 'asc':
        if sort_by == 'due_date':
            query = query.order_by(Task.due_date.is_(None), sort_column.asc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        if sort_by == 'due_date':
            query = query.order_by(Task.due_date.is_(None), sort_column.desc())
        else:
            query = query.order_by(sort_column.desc())

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    if per_page not in [9, 18, 27, 50]:
        per_page = 9

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('tasks.html', pagination=pagination)


@tasks_bp.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create a new task."""
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            category=form.category.data.strip() if form.category.data else None,
            estimated_minutes=form.estimated_minutes.data,
            priority=form.priority.data,
            status=form.status.data,
            due_date=form.due_date.data,
            owner=current_user
        )
        if form.status.data == 'Completed':
            task.completed_at = datetime.utcnow()
            
        process_tags(task, form.tags.data)
        
        db.session.add(task)
        db.session.commit()
        
        log_activity(current_user.id, 'Created Task', 'Task', task.id)
        db.session.commit()
        
        flash("Task created successfully!", "success")
        return redirect(url_for('tasks.list_tasks'))
    return render_template('task_form.html', form=form, title="Create New Task", action_url=url_for('tasks.create_task'))


@tasks_bp.route('/tasks/<int:task_id>')
@login_required
def view_task(task_id):
    """View details of a specific task."""
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id or task.is_deleted:
        abort(403)
    return render_template('task_detail.html', task=task)


@tasks_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id or task.is_deleted:
        abort(403)

    form = TaskForm(obj=task)
    if request.method == 'GET':
        form.tags.data = ", ".join([tag.name for tag in task.tags])

    if form.validate_on_submit():
        task.title = form.title.data.strip()
        task.description = form.description.data.strip() if form.description.data else None
        task.category = form.category.data.strip() if form.category.data else None
        task.estimated_minutes = form.estimated_minutes.data
        task.priority = form.priority.data
        
        if form.status.data == 'Completed' and task.status != 'Completed':
            task.completed_at = datetime.utcnow()
        elif form.status.data != 'Completed':
            task.completed_at = None
            
        task.status = form.status.data
        task.due_date = form.due_date.data
        
        process_tags(task, form.tags.data)
        
        log_activity(current_user.id, 'Updated Task', 'Task', task.id)
        db.session.commit()
        
        flash("Task updated successfully!", "success")
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    return render_template('task_form.html', form=form, title="Edit Task", action_url=url_for('tasks.edit_task', task_id=task.id))


@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Soft Delete a task."""
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id or task.is_deleted:
        abort(403)
    
    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    
    log_activity(current_user.id, 'Deleted Task', 'Task', task.id)
    db.session.commit()
    
    flash("Task deleted successfully!", "success")
    return redirect(url_for('tasks.list_tasks'))


@tasks_bp.route('/tasks/<int:task_id>/status', methods=['POST'])
@login_required
def update_task_status(task_id):
    """Quickly update the status of a task."""
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id or task.is_deleted:
        abort(403)

    new_status = request.form.get('status')
    if new_status in ['Pending', 'In Progress', 'Completed']:
        task.status = new_status
        if new_status == 'Completed':
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None
            
        log_activity(current_user.id, f'Marked Task as {new_status}', 'Task', task.id)
        db.session.commit()
        flash(f"Task status updated to {new_status}.", "success")
    else:
        flash("Invalid status provided.", "danger")
    
    return redirect(request.referrer or url_for('tasks.list_tasks'))


@tasks_bp.route('/tasks/bulk', methods=['POST'])
@login_required
def bulk_actions():
    """Perform bulk actions on selected tasks."""
    action = request.form.get('action')
    task_ids = request.form.getlist('task_ids')

    if not action or not task_ids:
        flash("No action or tasks selected.", "warning")
        return redirect(request.referrer or url_for('tasks.list_tasks'))

    tasks = current_user.tasks.filter(Task.id.in_(task_ids), Task.is_deleted == False).all()
    
    if not tasks:
        flash("No valid tasks found.", "danger")
        return redirect(request.referrer or url_for('tasks.list_tasks'))

    if action == 'delete':
        for task in tasks:
            task.is_deleted = True
            task.deleted_at = datetime.utcnow()
        log_activity(current_user.id, f'Bulk Deleted {len(tasks)} Tasks')
        db.session.commit()
        flash(f"Successfully deleted {len(tasks)} tasks.", "success")
        
    elif action in ['Pending', 'In Progress', 'Completed']:
        for task in tasks:
            task.status = action
            if action == 'Completed':
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None
        log_activity(current_user.id, f'Bulk Marked {len(tasks)} Tasks as {action}')
        db.session.commit()
        flash(f"Successfully marked {len(tasks)} tasks as {action}.", "success")
    else:
        flash("Invalid action.", "danger")

    return redirect(request.referrer or url_for('tasks.list_tasks'))


@tasks_bp.route('/tasks/export/<format>')
@login_required
def export_tasks(format):
    """Export tasks in CSV or JSON format."""
    tasks = current_user.tasks.filter_by(is_deleted=False).all()
    log_activity(current_user.id, f'Exported Tasks as {format.upper()}')
    db.session.commit()
    
    if format == 'csv':
        def generate():
            yield 'ID,Title,Description,Status,Priority,Category,Estimated_Minutes,Due_Date,Created_At,Completed_At\n'
            for t in tasks:
                desc = t.description.replace('\n', ' ').replace('\r', '') if t.description else ''
                category = t.category if t.category else ''
                due = t.due_date.isoformat() if t.due_date else ''
                created = t.created_at.isoformat()
                completed = t.completed_at.isoformat() if t.completed_at else ''
                yield f'{t.id},"{t.title}","{desc}",{t.status},{t.priority},"{category}",{t.estimated_minutes or ""},{due},{created},{completed}\n'
                
        return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=tasks.csv'})
        
    elif format == 'json':
        data = []
        for t in tasks:
            data.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'category': t.category,
                'estimated_minutes': t.estimated_minutes,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'created_at': t.created_at.isoformat(),
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
                'tags': [tag.name for tag in t.tags]
            })
        return Response(json.dumps(data, indent=2), mimetype='application/json', headers={'Content-Disposition': 'attachment; filename=tasks.json'})
        
    else:
        abort(400)
