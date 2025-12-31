# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """
    Pre-installation Checks:

    If the database already has: ir.config_parameter(key=ir_attachment.location)
    use that record to populate ir_model_data.
    :param cr:
    :param version:
    """
    cr = env.cr
    cr.execute("""
        select id from ir_config_parameter
        where key = 'ir_attachment.location'
    """.strip())
    any_found = cr.fetchone()
    if not any_found:
        return

    # Add to ir.model.data if not already there
    # - use SQL as it's all in an odd-state if the data is there (but the module hasn't been installed)

    module = "base_generic_changes"
    model = "ir.config_parameter"
    name = "config_attachment_location"  # id-name from data/ir-config-parameter.xml

    config_id = any_found[0]
    cr.execute("""
        select res_id from ir_model_data
        where module = %s
        and model = %s
        and name = %s
    """.strip(), (module, model, name))
    result = cr.fetchone()
    if not result:
        _logger.info(f"Adopt existing ir.config_parameter={config_id} into module")
        cr.execute(f"""
            insert into ir_model_data (module, model, name, res_id)
            values (%s, %s, %s, %s)
        """.strip(), (module, model, name, config_id))
        return

    res_id = result[0]
    if res_id != config_id:
        _logger.info(f"Correct ir.config_parameter={config_id} into module")
        cr.execute(f"""
            update ir_model_data set
              res_id = %s
            where module = %s
            and model = %s
            and name = %s
        """.strip(), (config_id, module, model, name))
    else:
        _logger.info(f"All good with existing ir.config_parameter={config_id}")
