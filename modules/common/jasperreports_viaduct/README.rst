JasperReports Viaduct
=====================

This module provides integration with `JasperReports <https://github.com/TIBCOSoftware/jasperreports>`_
as an alternative to using ``wkhtmltopdf`` for PDF report generation.

The module also provides read-only communication channel (a **viaduct**) to allow the JasperReport to
query Odoo for report-values to fill a report.

Configuration
-------------

The out-of-the-box defaults will allow Odoo to communicate with a Tomcat instance on port 8080
running the **jasperreports_viaduct** web-app. These can be overridden by adding a ``jasperreports_viaduct``
section in Odoo configuration file::

    [jasperreports_viaduct]

    # URL for this instance of Odoo
    odoo = http://localhost:8069

    # URL for the viaduct web-app instance
    viaduct = http://localhost:8080
