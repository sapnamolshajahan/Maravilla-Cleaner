ESC/POS Reports
===============

Summary
-------
Generate ESC/POS Reports with XML-ESCPOS_, a simple line-oriented XML for line-based reports.

Reports are defined as "qweb-text", with the report_filename of **escpos**. Specific printer-profiles can
be used by defining "escpos_reports.escpos_profile" in the Odoo context before generating the report.

This module reimplements XML-ESC/POS using python-escpos_ The original project site appears
abandoned.

CUPS Configuration
------------------
The printer type is "Raw".

If using network printing, use the ``lpd`` protocol. The printer url will be ``lpd://${host}/queue``.
Note that with the *lpd* protocol, only the ${host} is significant.

To add USB printers, first ensure that the printer has been connected and powered-up; before attempting
adding the printer via CUPS Admin.


.. _XML-ESCPOS: https://github.com/fvdsn/py-xml-escpos
.. _python-escpos: https://github.com/python-escpos/python-escpos
