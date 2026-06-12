from datetime import date
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.models import Task, Activity

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
def index():
    """Render public landing page if not logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    return render_template('index.html')


@core_bp.route('/dashboard')
@login_required
def dashboard():
    """Protected Dashboard landing view showing user task statistics and recent list."""
    # N+1 query optimization using joinedload for tags
    tasks_query = current_user.tasks.filter_by(is_deleted=False).options(joinedload(Task.tags))

    total_tasks = tasks_query.count()
    pending_tasks = tasks_query.filter(Task.status == 'Pending').count()
    in_progress_tasks = tasks_query.filter(Task.status == 'In Progress').count()
    completed_tasks = tasks_query.filter(Task.status == 'Completed').count()
    high_priority_tasks = tasks_query.filter(Task.priority == 'High').count()
    
    today = date.today()
    due_today_tasks = tasks_query.filter(Task.due_date == today, Task.status != 'Completed').count()
    overdue_tasks = tasks_query.filter(Task.due_date < today, Task.status != 'Completed').count()

    # Retrieve the latest 5 tasks
    recent_tasks = tasks_query.order_by(Task.created_at.desc()).limit(5).all()
    
    # Retrieve recent activities
    recent_activities = current_user.activities.order_by(Activity.timestamp.desc()).limit(10).all()

    return render_template(
        'dashboard.html',
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        high_priority_tasks=high_priority_tasks,
        due_today_tasks=due_today_tasks,
        overdue_tasks=overdue_tasks,
        recent_tasks=recent_tasks,
        recent_activities=recent_activities
    )


@core_bp.route('/calendar')
@login_required
def calendar():
    """Render calendar view for tasks."""
    tasks = current_user.tasks.filter(Task.is_deleted == False, Task.due_date != None).all()
    
    events = []
    for task in tasks:
        color = '#0d6efd' # primary
        if task.priority == 'High':
            color = '#dc3545' # danger
        elif task.priority == 'Medium':
            color = '#ffc107' # warning
            
        if task.status == 'Completed':
            color = '#198754' # success
            
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat(),
            'url': url_for('tasks.view_task', task_id=task.id),
            'color': color
        })
        
    return render_template('calendar.html', events=events)
