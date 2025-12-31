from odoo import models, api

class CarrierShipmentWizardInherit(models.TransientModel):
    _inherit = "carrier.shipment.wizard"

    def button_send_shipment(self):
        res = super().button_send_shipment()

        for wizard in self:
            carton_count = 0

            # 1. Standard box lines
            if wizard.detail_ids:
                carton_count += sum(line.qty for line in wizard.detail_ids)

            # 2. Custom boxes (only if the wizard has custom_boxes ticked)
            if wizard.custom_boxes:
                custom_boxes = self.env["carrier.shipment.custom.box"].search([
                    ("wizard_id", "=", wizard.id)
                ])
                carton_count += len(custom_boxes)

            pallet_count = wizard.pallet_qty or 0

            if wizard.picking_id:
                wizard.picking_id.write({
                    "carton_qty": carton_count,
                    "pallet_qty": pallet_count,
                })

        return res

