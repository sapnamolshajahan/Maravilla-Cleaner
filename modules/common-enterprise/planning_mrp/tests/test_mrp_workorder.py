import pytz
from odoo.tests.common import TransactionCase, tagged
from datetime import datetime, timedelta

@tagged('common', 'planning_mrp')
class TestMRPWorkOrderPlanningSlot(TransactionCase):

    def setUp(self):
        super(TestMRPWorkOrderPlanningSlot, self).setUp()
        self.WorkOrder = self.env['mrp.workorder']
        self.Production = self.env['mrp.production']
        self.Bom = self.env['mrp.bom']
        self.Product = self.env['product.product']
        self.Role = self.env['planning.role']

        self.work_center = self.env['mrp.workcenter'].create({"name": "WorkCenter 3", "time_start": 13})

        self.product = self.Product.create({
            'name': 'Test Product',
            'type': 'service',
        })

        self.bom = self.Bom.create({
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
            'bom_line_ids': [],
            'code': 'BOM-Test',
        })

        self.production = self.Production.create({
            'product_id': self.product.id,
            'product_uom_id': 1,
            'product_qty': 1,
            'bom_id': self.bom.id,
            'state': 'confirmed',
        })

        self.workorder_vals = {
            'production_id': self.production.id,
            'product_uom_id': 1,
            'workcenter_id': self.work_center.id,
            'name': 'WO Test',
            'date_start': datetime.now(),
            'date_finished': datetime.now() + timedelta(hours=2),
        }

        self.role = self.Role.create({
            'name': 'Work Order Role',
            'usage': 'workorder',
        })

    def test_create_workorder_creates_planning_slot(self):
        workorder = self.WorkOrder.create(self.workorder_vals)
        workorder.get_planning_slot()
        self.assertTrue(workorder.planning_slot_id, "Planning slot should be created on work order creation.")

    def test_create_without_dates_uses_default_planning_range(self):
        workorder_vals = self.workorder_vals.copy()
        workorder_vals.pop('date_start', None)
        workorder_vals.pop('date_finished', None)

        workorder = self.WorkOrder.create(workorder_vals)
        workorder.get_planning_slot()
        self.assertTrue(workorder.planning_slot_id, "Planning slot should be created using default date range")

    def test_multiple_workorder_write_creates_or_updates_slots(self):
        workorder1 = self.WorkOrder.create(self.workorder_vals)
        workorder2_vals = self.workorder_vals.copy()
        workorder2_vals['name'] = 'WO 2'
        workorder2 = self.WorkOrder.create(workorder2_vals)

        new_date = datetime.now() + timedelta(days=1, hours=3)
        workorder1.write({'date_finished': new_date})
        workorder2.write({'date_finished': new_date})

        workorder1.get_planning_slot()
        workorder2.get_planning_slot()

        self.assertEqual(workorder1.planning_slot_id.end_datetime.date(), new_date.date())
        self.assertEqual(workorder2.planning_slot_id.end_datetime.date(), new_date.date())
