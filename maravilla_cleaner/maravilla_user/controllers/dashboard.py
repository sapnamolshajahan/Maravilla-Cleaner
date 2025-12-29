from odoo import http
from odoo.http import request
from datetime import datetime,timedelta,date
import logging

_logger = logging.getLogger(__name__)

class WebsiteDashbaord(http.Controller):

    @http.route('/website/dashboard', type='http', auth='public', website=True)
    def website_dashboard(self, **kw):
        user = request.env.user

        # Get employee linked to user (FSM Tasks are assigned to employees)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        upcoming = in_progress = completed = 0

        if employee:
            task_model = request.env['project.task'].sudo()

            # Upcoming = Planned tasks (no start yet)
            upcoming = task_model.search_count([
                ('user_ids', 'in', user.id),
                ('stage_id.name', 'ilike', 'New')
            ])

            # In Progress = Stage contains "Progress"
            in_progress = task_model.search_count([
                ('user_ids', 'in', user.id),
                ('stage_id.name', 'ilike', 'Progress')
            ])

            # Completed = Done tasks
            completed = task_model.search_count([
                ('user_ids', 'in', user.id),
                ('stage_id.name', '=', 'Done')
            ])

        return request.render("maravilla_user.dashboard_page", {
            'upcoming': upcoming,
            'in_progress': in_progress,
            'completed': completed,
        })

    @http.route('/website/dashboard/tasks_by_date', type='jsonrpc', auth='user', website=True)
    def get_tasks_by_date_range(self, end_date=None, **kw):
        """Get tasks count from current date to selected end date"""
        user = request.env.user
        print(end_date)
        # Convert string date to datetime object
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()

        # Start date is always today
        start_date = datetime.now().date()

        _logger.info(f"Fetching tasks from {start_date} to {end_date}")

        task_model = request.env['project.task'].sudo()

        # Get all tasks for the user within date range
        # Assuming tasks have a date_deadline or date_start field
        # You might need to adjust this based on your actual task date fields

        # Option 1: If tasks have date_deadline field
        upcoming = task_model.search_count([
            ('user_ids', 'in', user.id),
            ('stage_id.name', 'ilike', 'New'),
            ('date_deadline', '>=', start_date),
            ('date_deadline', '<=', end_date),
        ])

        in_progress = task_model.search_count([
            ('user_ids', 'in', user.id),
            ('stage_id.name', 'ilike', 'Progress'),
            ('date_deadline', '>=', start_date),
            ('date_deadline', '<=', end_date),
        ])

        if isinstance(end_date, str):
            day_start = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            # Already a date → convert to datetime
            day_start = datetime.combine(end_date, datetime.min.time())

        day_end = day_start + timedelta(days=1)

        completed = task_model.search_count([
            ('user_ids', 'in', user.id),
            ('stage_id', '=', 3),  # Completed stage,
            ('write_date', '>=', day_start),
            ('write_date', '<=', day_end),
        ])

        print("date start",day_start)
        print("date end",day_end)

        return {
            'upcoming': upcoming,
            'in_progress': in_progress,
            'completed': completed,
            'date_range': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        }




