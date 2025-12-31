POS Receipt
===========

This module implements sample POS Receipt using two alternative methods:

1. ESC/POS XML: pos_receipt.pos_receipt_report
2. Label Printer Templates: pos_receipt.pos_receipt_label

An introduced method **pos.order** ``get_pos_receipt_report()`` returns a reference
to the **ir.actions.report** used to render the POS Receipt. This module uses
**pos_receipt.pos_receipt_report** by default.

Customisations may be based on either the ESC/POS version or the **label.printer.template** implementation,
and overriding ``get_pos_receipt_report()``.
