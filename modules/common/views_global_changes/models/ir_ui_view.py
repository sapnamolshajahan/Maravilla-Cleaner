from odoo import models, api
from odoo.tools.safe_eval import safe_eval

class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def postprocess(self, model, node, view_id, in_tree_view, model_fields):
        res = super(IrUiView, self).postprocess(model, node, view_id, in_tree_view, model_fields)
        param = self.env['ir.config_parameter'].sudo().get_param('views_global_changes.disable_m2o_create_edit')
        if param == 'True':
            if type(node.tag) == str:
                if node.tag == 'field':
                    field = model_fields.get(node.get('name'))
                    if field:
                        if field['type'] in ['many2one', 'many2many']:
                            if node.get('options'):
                                options = safe_eval(node.get('options'), locals_dict={'true': True, 'false': False})
                                if options.get('allow_create'):
                                    return res
                            node.set("options", "{'no_create':True}")

        return res
