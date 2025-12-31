# JasperReports and Viaduct

## Basic Operation

JasperReports divides a report into the following base-sections:

* title-header
* column-header
* detail-line
* column trailer
* summary

Just prior to printing _each_ detail line, it decides on whether it needs to print any of the other
sections first, and then prints the detail-line. Once it reaches the end of the input-stream,
it will then print the end-sections and finish up. Aside from the base-sections, additional *Group Header* and
*Group Trailer* sections can be added and printed when *Trigger Conditions* are met.

The most common use-case for JasperReports is extract data from a database using an SQL query and then
displaying the results in a desired layout. The SQL query is composed to generate the **detail** lines for a
report. This is a *critical* point. If the query results in an empty set, then **no** report is generated.

## Viaduct Expressions

The main problem with using JasperReports with SQL is that data extraction query must include a field in order
to display the value on the report. This can lead to very cumbersome SQL expressions, very often with multiple joins
across many tables. The developer is often required to decode a complicated expression before being able to
add additional data-fields to the SQL.

This method of composing reports is discouraged when composing reports with **jasperreports_viaduct**. The more
common design pattern is to use **Viaduct Expressions**. **Viaduct Expressions** uses a communication channel
to consult the Odoo instance to generate values for a display element. In order to display a field value, an
expression similar to the following is used instead:

```
$P{viaduct}
  .helper ("line", $F{id})
  .get ("name")
```

The **$P{viaduct}** object provides a channel to the Odoo instance. In this case, **viaduct** will consult the
*report_helper* associated with the report; invoking the helper's `line` method with a `id` argument. The helper
returns a dictionary of values, of which the **name** attribute value is what will be displayed. The **viaduct**
channel is provided to the JasperReports engine by the webapp.

The introduction of a two-way channel simplifies the SQL expressions assocated with the datasource. In the case
of a invoice-report, the original SQL query to display detail lines (as well as the company, partner, and other
linked tables) would be something like:

```
select
  account_move.name "invoice-number"
  account_move.ref,
  ...
  account_move_line.name "detail",
  account_move_line.credit,
  ...
  res_company.name "company-name",
  res_partner.name "partner-name",
  ...
from account_move, account_move_line, res_company, res_partner, res_partner address, ...
where account_move.id = $P{move-id}
and account_move_line.move_id = account_move.id
and res_company.id = account_move.company_id
and res_partner.id = account_move.partner_id
and address.parent_id = res_partner.id
and address.type = 'contact'
and ...
```

With the use of **Viaduct Expressions**, the SQL is simplified to:

```
select
  account_move.id "invoice-id",
  account_move_line.id "line-id"
from account_move, account_move_line
where account_move.id = $P{move-id}
and account_move_line.move_id = account_move.id
```

The *report_helper* populates a data-dictionary for a given _id_ value, and JasperReports displays the value
by consulting the **viaduct** channel, eg:

```
$P{viaduct}.helper ("invoice", $F{invoice-id}).get ("name")
$P{viaduct}.helper ("invoice", $F{invoice-id}).get ("ref")
$P{viaduct}.helper ("invoice", $F{invoice-id}).get ("company")
$P{viaduct}.helper ("line", $F{line-id}).get ("name")
$P{viaduct}.helper ("line", $F{line-id}).get ("credit")
$P{viaduct}.helper ("line", $F{line-id}).get ("debit")
```


