# Remote Print MQTT Agent

This is a standalone program that will:

1. listen for job-notifications on a MQTT broker
2. retrieve the print jobs from the Odoo Instance
3. submit them to a local CUPS service.

## Configuration file

An example configuration file:

```
[agent]

# required: MQTT broker URL {mqtt|mqtt+ssl}://[username:password@]hostname[:port]
# - schemes: "mqtt" or "mqtt+ssl"
# - optional username + password
# - port default: "mqtt" 1833, "mqtt+ssl" 8883
broker = mqtt://mqtt.odooplus.nz

# required
private_key = /path/to/key-private.pem

# required: space-separated list of odoo_urls
odoo_urls = https://odoo.instance https://uat.odoo.instance

# required: space-separated list of local print-queues
queues = queue-1 queue-2 queue-3
    
# optional: lp command string, placeholders {queue} and {path} are mandatory
lp_command = lp -d {queue} {path}

# optional: logging level; debug, info, warning, error
log_level = info
```

The private key is generated with `openssl`:

```
$ openssl genrsa -out private.pem 2048
$ openssl rsa -in private.pem -outform PEM -pubout -out public.pem 
```

## Protocol Overview

### Startup

For each configured Odoo instance, the client will submit the following:

* client hostname
* list of queues that the client will accept
* session identifier
* signature for the session identifier, signed with the client's private key

It expects to receive the following:

* an MQTT topic for each queue's print notification

The client will then:

1. subscribe to each queue-notification topic
2. ask the Odoo instance for a query-token for each queue

### Printing

When the client receives a message on the queue-notification topic, it:

1. decrypts the notification; ignoring the notification if this fails
2. the decrypted notification contains:
    * queue
    * queue query-token
1. the client uses the queries the Odoo instance for a list of job-entries on the queue
1. Odoo returns a list of job query-tokens
1. the client retrieves the job using the query token and submits it to CUPS
