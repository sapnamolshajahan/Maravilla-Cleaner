# Developer Guide

## Structure

* **odoo** : a snapshot of [Odoo](https://github.com/odoo/odoo)
* **enterprise** : a snapshot of [Odoo Enterprise](https://github.com/odoo/enterprise)

* **modules/common** : OptimySME standard modules
* **modules/common-enterprise** : OptimySME modules requiring Odoo Enterprise
* **modules/community** : third-party modules
* **modules/never-production** : modules that should never be installed on
*Production* systems.

* **etc/requirements** : python requirements for developer use
* **etc/odoo-patches** : Local tweaks to standard Odoo
* **etc/unittests** : rc files for CI server
* **etc/*** : personal developer rc files

### Customer

* **customer/release-config.sh** : deployment configuration file
* **customer/*/modules** : customer specific modules

## Tools

The primary IDE used by OptimySME is [PyCharm](https://www.jetbrains.com/pycharm/).
Please configure the following to standardise development for all developers:

* Settings > Tools > Actions on Save

    * *Reformat code* (All file types)
    * *Optimyze imports* (All file types)

Additionally, the following plugin should be installed:

* [Odoo IDE](https://plugins.jetbrains.com/plugin/13499-odoo-ide)

## Testing

We primarily focus on Python Unit tests within the code base. Start with
[Testing Odoo](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html).

Additionally, a wrapper script is provided to test a module:

* `bin/test-module config module [test-db]`

This script will run the tests and evaluate the test-coverage. It must be
run from the root of the repository, and accepts the following arguments:

* **config**: path to a usable configuration file, which should contain
at the minimum, a valid *addons_path* and *db_user*.

* **module**: the module to test.

* **test-db**: if provided, the tests will be run using this database. If
this argument is not provided, a database will be created to run the
module's tests, and it will be removed when the tests complete.

The test-output can be found in:

* **tests-output/html** : coverage report
* **tests-output/xmlrunner** : individual test-output
