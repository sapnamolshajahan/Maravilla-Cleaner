# Building Report Helpers

## Basic Usage

Report Helpers provide data-values for **Viaduct Expressions**. When a report uses the expression, eg:

```
$P{viaduct}
  .helper ("line", $F{id})
  .get ("name")
```

the application will consult the report-helper in Odoo associated with the report for evaluation. For this
example, the associated report_helper snippet will look something like:

```
class ReportHelper(ViaductHelper):
    ...

    def line(self, line_id):
        line = self.env["account.move.line"].browse(line_id)
        result = {
            ...
        "name": line.name,
        ...
        }
        return result
```

report_helpers are standard Python classes, using standard Python inheritance. They are **not** Odoo models.
All JasperReports have an associated report_helper. It is possible for a JasperReport to work without an
associated report_helper, but this situation would most likely be an error.

JasperReports are associated to a report_helper via the **report_name** attribute of `ir.actions.report`. For
example, if there is a XML declaration:

```
<record id="move_report" model="ir.actions.report">
    <field name="name">Account Move Report</field>
    <field name="report_name">
        odoo.addons.jasperreports_viaduct.reports.viaduct_test_helper.ViaductTestHelper
    </field>
    <field name="report_file">jasperreports_viaduct/reports/move-unpack.jrxml</field>
    <field name="model">account.move</field>
    <field name="binding_model_id" ref="accounts.model_account_move"/>
</record>
```

An instance of the named report_helper will be spun up to handle data-requests from Tomcat when it
runs the report.

The **jasperreports_viaduct** module has `odoo.addons.reports.common_helper.CommonHelper` which defines
some useful methods used by many report_helpers.

## Custom Reports

In many cases, a customer may eschew the out-of-the-box report documents for a customised version with layout
changes and additional data-fields. The current best practise is to:

1. create a customer module eg: `cust1_invoice_report`
2. copy the jrxml files from the base report into the new module
3. create a (possibly empty) custom report_helper for the custom report
4. create `ir.actions.report` XML entries for the new report
5. disable the `ir.actions.report` for the out-of-the-box report.
6. use *JasperReports Studio* to customise the report

If we have a fictional customer of _Customer1_ who wanted a custom invoice-report, we would first create a
new module `cust1_invoice_report`, and copy over the `.jrxml` files from `account_invoice_reports`.

A new report_helper for the custom report would be defined as a subclass of the `StandardInvoiceHelper`,
eg: in `reports/invoice_helper.py`:

```
from odoo.addons.account_invoice_reports.reports.invoice_helper import StandardInvoiceHelper

class Cust1InvoiceHelper(StandardInvoiceHelper):

    pass
```

Define the required XML entries:

```
<!-- Deactivate the standard invoice report -->
<record id="account_invoice_reports.standard_invoice_viaduct" model="ir.actions.report">
    <field name="binding_model_id" eval="False"/>
</record>

<!-- Custom Invoice report -->
<record id="cust1_invoice_viaduct" model="ir.actions.report">
    <field name="name">Customer1 Invoice</field>
    <field name="report_name">
        odoo.addons.cust1_invoice_report.reports.invoice_helper.Cust1InvoiceHelper
    </field>
    <field name="report_file">cust1_invoice_report/reports/invoice-unpack.jrxml</field>
    <field name="model">account.move</field>
    <field name="binding_model_id" ref="accounts.model_account_move"/>
</record>
```

If new **Viaduct Expressions** are required, update `Cust1InvoiceHelper` as required, eg:

```
class Cust1InvoiceHelper(StandardInvoiceHelper):

    def line(self, line_id):
        line = self.env["account.invoice.line"].browse(line_id)
        
        result = super(Cust1InvoiceHelper, self).line(line_id)
        result["some-new-value"] = self.compute_some_new_value(line)
        return result

```
