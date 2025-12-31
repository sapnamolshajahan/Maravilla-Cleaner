Label Printing
===============

Simple Framework for Label Printing.

The currently supported Printer Languages are:

- DPL - Datamax
- TSPL - TSC Printronix
- ZPL - Zebra Technologies
- SBPL - Sato

Use templates to provide layout and introduce markup to embed model-values into Jinja2 templates. This reduces
the implementation required for printer specific features. The template is rendered using syntax and semantics
described by https://jinja.palletsprojects.com/en/stable/templates/

A singleton recordset and the corrent context is supplied to template for rendering. These can be referenced
within the template as **obj** and **context**, eg::

    Address field on obj: {{obj.address or ''}}
    Control Character EOT: {{"\x4"}}
    Browser language: {{context.lang}}

Printer-specific expressions are enclosed within ``{<`` and ``>}``. These may be common to all printer-types,
or may be specific to a particular type. The current set of common expressions are:

{<SOH>} {<STX>} {<ESC>}
    Replace with ASCII character
{<img:*expression*>}
    TO-DO: Include an image using ``byte[]`` from the *expression*, eg: ``{<img:obj.logo>}``

Label Reports
-------------

For most part the Framework prints directly to system-queue printers. However, it can also be integrated into
the Odoo Report Framework using XML, eg::

    <!--
        Label Template reports require:
            - report_file=label.printer.template
            - report_type=qweb-text
            - report_name=${latest active label.printer.template:name to use}
      -->
    <record id="a_custom_label" model="ir.actions.report">
        <field name="name">Name of Label)</field>
        <field name="report_name">this.name.must.match.the.template.name</field>
        <field name="report_file">label.printer.template</field>
        <field name="report_type">qweb-text</field>
        <field name="model">model.name</field>
        <field name="binding_model_id" ref="point_of_sale.model_pos_order"/>
    </record>
    <record id="a_custom_label_template" model="label.printer.template">
        <field name="name">this.name.must.match.the.template.name</field>
        <field name="description">A label</field>
        <field name="flavour">escpos</field>
        <field name="model">model.name</field>
        <field name="content"><![CDATA[...]]></field>
    </record>
