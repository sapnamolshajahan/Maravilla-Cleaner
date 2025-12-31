# JasperReports Viaduct

The **jasperreports_viaduct** module integrates the [JasperReports](https://github.com/TIBCOSoftware/jasperreports)
with Odoo. [JasperReports](https://github.com/TIBCOSoftware/jasperreports) is an open-source Java based reporting
engine, complete with a Report Designer UI, capable of producing pixel-perfect documents in a variety of document
formats including HTML, PDF, Excel, OpenOffice and MS Word.

The system consists of 2 components:

- **jasperreports-viaduct18** - a Java webapp that accepts report data and renders the output using the JasperReports
  engine.
- **jasperreports_viaduct** - this module, which relays data from Odoo to the Java webapp and retrieves the rendered
  output.

## Information Links

* [Webapp Installation](doc/install-webapp.md)
* [Odoo Configuration](doc/odoo-config.md)
* Developers
    * [Setup and Running a Test Instance](doc/setup.md)
    * [JasperReports Basics](doc/jasper.md)
    * [XML Files](doc/xml-files.md)
    * [Using JasperSoft Studio](doc/jstudio.md)
    * [Building Report Helpers](doc/report-helper.md)

