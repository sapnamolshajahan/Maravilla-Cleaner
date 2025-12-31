Auto-Print POS Receipt
======================

This module enables a POS Receipt to be automatically printed once Payment is completed.
This implementation relies on the Odoo backend to control the printing, and not the
POS front-end.

Configuration Notes
-------------------

Each POS Configuration requires:

* autoprint_invoice : boolean
* pos_invoice_queue : queue name

Technical Notes
---------------

The POS front-end is overridden to call backend end-points for printing; this
includes opening the cashbox, which is usually connected to the receipt-printer.
