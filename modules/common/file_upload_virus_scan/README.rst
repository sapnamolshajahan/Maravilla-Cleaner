File Upload Virus Scan
======================

Check uploaded files for virii, using `ClamAV <https://www.clamav.net>`.

Configuration
-------------

By default, ``file_upload_virus_scan`` will connect to ``clamd`` on the current host. To
connect a remote host, add the following section to the Odoo configuration file::

    [file_upload_virus_scan]

    # remote host; required
    clamav_host = clamav.host
    # tcp/ip port; default=3310
    clamav_port = 3310

