# XML and JRXML files

## Odoo XML entries

The **jasperreports_viaduct** module piggybacks off the Odoo's `ir.actions.report` with the default
**report_type** of *qweb-pdf*. The module inspects the the **report_name** field whenever a *qweb-pdf* report
is requested, and if it ends with `.viaduct`, it will use JasperReports to render the report.

The JasperReport input file (jrxml) is usually located in a module's `reports` subdirectory, and must be
specifed in Odoo's XML declaration; eg:

```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="viaduct_test_report" model="ir.actions.report">
        <field name="name">Viaduct Test Report</field>
        <field name="report_name">test.report.viaduct</field>
        <field name="report_file">jasperreports_viaduct/reports/viaduct-test-report.jrxml</field>
        <field name="model">res.company</field>
        <field name="binding_model_id" ref="base.model_res_company"/>
    </record>
</odoo>
```

## The jrxml-unpack pattern

In its simplest form, a JRMXL file will contain a report that will present output for a list of id-values. Odoo
may request a report for one or more id-values (eg: a list of invoices, a list of packing slips). JasperReports
can handle this, but will require the use of *Group Headers and Trailers* as well associated *Trigger Conditions*.
It is *much* simpler for a developer to design a report for just **ONE** id-value at a time; as a lot of
additional checks can be discarded.

To facilitate this, a common design pattern is to use a `-unpack.jrxml` report that will JasperReport's
**subreports** feature to decompose the report. The use of an `-unpack.jrxml` also provides the opportunity
to have different report layouts depending on the data-attributes.

For example, when presented with a list of `account.move` records, the requirement may be to print out Invoices or
Credit-Notes, depending on the value of `account.move` **move_type**. A possible solution would be to have the
following files:

* move-unpack.jrxml
* invoice.jrxml
* credit.jrxml

The Odoo XML declaration refer to the top-level report, `move-unpack.jrxml`:

```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
	<record id="move_report" model="ir.actions.report">
		<field name="name">Account Move Report</field>
		<field name="report_name">account.move.viaduct</field>
		<field name="report_file">jasperreports_viaduct/reports/move-unpack.jrxml</field>
        <field name="model">account.move</field>
		<field name="binding_model_id" ref="accounts.model_account_move"/>
	</record>
</odoo>
```

The `move-unpack.jrxml` will inspect the `account.move` list and call either `invoice.jrxml` or `credit.jrxml`
as a **subreport** for each value depending on the **move_type** value.

The SQL datasource expression would then be:

```
select
  id,
  case move_type
  when 'out_refund' then 'credit'
  else 'invoice'
  end as report
from account_move
where $X{IN, id, viaduct-report-ids}
order by id
```

And the associated **subreport** expression:

```
$P{viaduct-directory} + "/" + $F{report} + ".jasper"
```

It will also hand the `account.move` id value to the **subreport** as **$P{move-id}**.

The SQL datasource expression in `invoice.jrxml` and `credit.jrxml` will then be:

```
select
  account_move.id "invoice-id",
  account_move_line.id "line-id"
from account_move, account_move_line
where account_move.id = $P{move-id}
and account_move_line.move_id = account_move.id
```

Note that the SQL expression is designed to for list out `account.move.line` as that's where the interesting
information lies. If there are no lines associated with the `account.move`, no report will be generated.