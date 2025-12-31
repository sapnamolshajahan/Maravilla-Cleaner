# Using JasperSoft Studio

[JasperSoft Studio](https://community.jaspersoft.com/project/jaspersoft-studio) is the UI for editing JasperReports XML
files and is available for download at [SourceForge](https://sourceforge.net/projects/jasperstudio/). The tool is
finicky, buggy and non-intuitive. However, it is also the only tool available to modify the XML input files
without extensive references.

The tool is useful for previewing and validating the position of display elements, as well as updating the various
attributes with the correct values. It has a lot of complex features, but we only use the following basic features:

* sql statement review
* report element positioning and attributes changes

The Studio cannot be used to generate output directly, as it needs to communicate with an active Odoo session for data
retrieval.

## Quick Tips:

* Use "File Open" to open the JRXML files. This will create a internal file-link when you open the file.
* The UI doesn't handle multiple files with the same name well, so remove the links when you are done.
* After changing a value, tab **off** the element in order to view the change
* When creating a new report, copy an existing template and then modify to suit
* Save layouts and then re-run the report from Odoo to view the final output
* Don't generate output using **Studio**. It will not work.
