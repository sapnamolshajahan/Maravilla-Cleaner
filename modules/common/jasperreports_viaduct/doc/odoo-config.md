# Configuration

## Standard

The *server_wide_modules* entry in Odoo's configuration file needs to be extended to include **jasperreports_viaduct**
for a fully functional system, ie:

```
[options]
...
# Modules offering multi-db support
server_wide_modules = base,web,jasperreports_viaduct

```

This configuration entry is only required if the running Odoo instance is making use of the multi-database feature.

## External Server

If the viaduct server not running on the same server as the Odoo instance, a `jasperreports_viaduct` section will
need to be added, eg:

```
[jasperreports_viaduct]

# URL for this instance of Odoo.
# This is not required if the Odoo instance's hostname and DNS agree with each other
odoo = http://localhost:8069

# URL for the viaduct web-app instance
# The default value is show,n and may be modified to suit
viaduct = http://localhost:8080
```
