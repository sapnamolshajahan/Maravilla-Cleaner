# Migrating to Odoo 19

This guide lists changes from previous versions of Odoo that requires re-work.

## odoo.tools.config

The Odoo configuration inspector, `odoo.tools.config`, will now only inspect and validate the [options]
section. All other (non-standard) sections are ignored, and the `get_misc()` method has been removed.

As a replacement, `base_generic_changes.utils.config.configuration` can be used to access non-standard
sections. This is a standard Python [ConfigParser](https://docs.python.org/3/library/configparser.html)
that parses the supplied **Odoo-rc** file.

**NOTE**: This adds a **base_generic_changes** as a dependency.

Example conversion:

*Old*:
```
from odoo.tools.config import config

SECTION_NAME = "remote_print_mqtt"
KEY_BROKER = "broker"
KEY_LP_CMD = "lp_command"

DEFAULT_LP_CMD = "lp -d {queue} -n {copies} {path}"

BROKER = config.get_misc(SECTION_NAME, KEY_BROKER)
LP_CMD = config.get_misc(SECTION_NAME, KEY_LP_CMD, DEFAULT_LP_CMD)
```

*New*:
```
from odoo.addons.base_generic_changes.utils.config import configuration

SECTION_NAME = "remote_print_mqtt"
KEY_BROKER = "broker"
KEY_LP_CMD = "lp_command"

DEFAULT_LP_CMD = "lp -d {queue} -n {copies} {path}"

BROKER = configuration.get(SECTION_NAME, KEY_BROKER)
LP_CMD = configuration.get(SECTION_NAME, KEY_LP_CMD, fallback=DEFAULT_LP_CMD)
```
