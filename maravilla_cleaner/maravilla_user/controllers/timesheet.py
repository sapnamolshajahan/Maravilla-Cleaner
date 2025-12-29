from odoo import http

import json
import logging

from odoo.http import request, Response

from datetime import datetime
import traceback

_logger = logging.getLogger(__name__)


class TimesheetAPI(http.Controller):

    @http.route('/api/timesheet/create', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_timesheet(self, **kwargs):
        try:
            # Get data from request
            data = request.jsonrequest
            _logger.info("Timesheet API called with data: %s", data)

            task_id = data.get('task_id')
            date = data.get('date')
            hours = data.get('hours')
            description = data.get('description')

            # Validate required fields
            if not all([task_id, date, hours, description]):
                return {
                    'success': False,
                    'error': 'Missing required fields: task_id, date, hours, description'
                }

            # Get the task
            task = request.env['project.task'].browse(int(task_id))
            if not task.exists():
                return {
                    'success': False,
                    'error': f'Task {task_id} not found'
                }

            # Get current user's employee
            employee = request.env.user.employee_id
            if not employee:
                return {
                    'success': False,
                    'error': 'No employee found for current user'
                }

            # Create timesheet
            timesheet = request.env['account.analytic.line'].create({
                'task_id': task.id,
                'project_id': task.project_id.id,
                'date': date,
                'unit_amount': float(hours),
                'name': description,
                'employee_id': employee.id,
            })

            _logger.info("Timesheet created successfully: %s", timesheet.id)

            return {
                'success': True,
                'timesheet_id': timesheet.id,
                'message': f'Timesheet created successfully for Task {task.name}'
            }

        except Exception as e:
            _logger.error("Error creating timesheet via API: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/timesheet/test', type='http', auth='user', methods=['GET'])
    def test_api(self, **kwargs):
        return request.make_response(json.dumps({
            'status': 'API is working',
            'user': request.env.user.name
        }), headers=[('Content-Type', 'application/json')])

    @http.route('/website/task/start', type='jsonrpc', auth='user', website=True, csrf=False)
    def website_task_start(self, **kwargs):
        try:
            task_id = kwargs.get('task_id')
            if not task_id:
                return {'jsonrpc': '2.0', 'error': {'code': -32602, 'message': 'task_id required'}, 'id': 1}

            task = request.env['project.task'].sudo().browse(int(task_id))
            if not task.exists():
                return {'jsonrpc': '2.0', 'error': {'code': -32602, 'message': 'Task not found'}, 'id': 1}

            employee = request.env.user.sudo().employee_id
            if not employee:
                return {'jsonrpc': '2.0', 'error': {'code': -32602, 'message': 'No employee linked to your user'},
                        'id': 1}

            Timesheet = request.env['account.analytic.line'].sudo()

            timesheet = Timesheet.create({
                'task_id': task.id,
                'project_id': task.project_id.id if task.project_id else False,
                'employee_id': employee.id,
                'name': f'Working on: {task.name}',
                'unit_amount': 0,
                'x_timer_start': datetime.now(),  # ✅ CUSTOM FIELD (IMPORTANT)
            })

            task.with_context(
                active_model='project.task',
                active_id=task.id,
                active_ids=[task.id],
                employee_id=employee.id,
            ).action_timer_start()

            return {
                'jsonrpc': '2.0',
                'result': {
                    'success': True,
                    'message': 'Timer started',
                    'timesheet_id': timesheet.id
                },
                'id': 1
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'jsonrpc': '2.0', 'error': {'code': -32603, 'message': str(e)}, 'id': 1}

    @http.route('/website/task/stop', type='jsonrpc', auth='user', website=True, csrf=False)
    def website_task_stop(self, **kwargs):
        try:
            task_id = kwargs.get('task_id')
            timesheet_id = kwargs.get('timesheet_id')

            task = request.env['project.task'].sudo().browse(int(task_id))
            employee = request.env.user.sudo().employee_id

            task.with_context(
                active_model='project.task',
                active_id=task.id,
                active_ids=[task.id],
                employee_id=employee.id,
            ).action_timer_stop()

            Timesheet = request.env['account.analytic.line'].sudo()

            if timesheet_id:
                timesheet = Timesheet.browse(int(timesheet_id))
            else:
                timesheet = Timesheet.search([
                    ('task_id', '=', task.id),
                    ('employee_id', '=', employee.id)
                ], order='id desc', limit=1)

            if timesheet:
                start_time = timesheet.x_timer_start or timesheet.create_date  # ✅ SAFE BACKUP

                delta = datetime.now() - start_time
                hours_logged = round(delta.total_seconds() / 3600, 2)

                timesheet.sudo().write({
                    'unit_amount': hours_logged,
                    'x_timer_stop': datetime.now()
                })
            else:
                hours_logged = 0

            return {
                'jsonrpc': '2.0',
                'result': {
                    'success': True,
                    'message': 'Timer stopped',
                    'hours': hours_logged
                },
                'id': 1
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'jsonrpc': '2.0', 'error': {'code': -32603, 'message': str(e)}, 'id': 1}
