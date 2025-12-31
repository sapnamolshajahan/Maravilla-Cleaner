Remote Printing
===============

Provide remote-printing capabilities for Odoo instances that are not
located on the same network as the printer.

This implementation uses an MQTT broker for print-job handover.

Odoo Configuration
------------------

Generate a passwordless RSA public/private key, eg::

    $ openssl genrsa -out private.pem 2048
    $ openssl rsa -in private.pem -outform PEM -pubout -out public.pem

In a nutshell::

    [options]
    ...
    # modules offering multi-db support
    server_wide_modules = base,web,remote_print_mqtt
    ...

    [remote_print_mqtt]

    # required: MQTT broker URL {mqtt|mqtt+ssl}://[username:password@]hostname[:port]
    # - schemes: "mqtt" or "mqtt+ssl"
    # - optional username + password
    # - port default: "mqtt" 1833, "mqtt+ssl" 8883
    broker = mqtt://mqtt.odooplus.nz

    # required
    topic_base = remote_print_mqtt/some-random-string

    # required: space-separated public keys of permitted print-servers
    remote_public_keys = public-1.pem public-2.pem public-3.pem

The `topic_base` value must be unique per organisation within the `broker`.

Remote Print Agent
------------------

A remote print agent running on the remote network will retrieve print-jobs from the Odoo server and print
to printers located on the remote network. The agent needs to be running a host on the remote network with
a locally configured CUPS server. The agent runs off a script, accepting a configuration file as an argument::

    $ remote_print_agent.py config-file

An example configuration file::

    [agent]

    # required: MQTT broker URL {mqtt|mqtt+ssl}://[username:password@]hostname[:port]
    # - schemes: "mqtt" or "mqtt+ssl"
    # - optional username + password
    # - port default: "mqtt" 1833, "mqtt+ssl" 8883
    broker = mqtt://mqtt.odooplus.nz

    # required: path to private-key
    private_key = /path/to/key-private.pem

    # required: space-separated list of odoo_urls
    odoo_urls = https://odoo.instance https://uat.odoo.instance

    # required: space-separated list of local print-queues
    queues = queue-1 queue-2 queue-3

    # optional: lp command string, placeholders {queue} and {path} are mandatory
    lp_command = lp -d {queue} {path}

    # optional: logging level; debug, info, warning, error
    log_level = info

