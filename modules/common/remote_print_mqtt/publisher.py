# -*- coding: utf-8 -*-
import json
import logging
import ssl
import uuid
from urllib.parse import urlparse

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from paho.mqtt import client as mqtt

from .config import BROKER, TOPIC_BASE, SECTION_NAME, KEY_BROKER, KEY_TOPIC_BASE, PROTOCOL_VERSION
from .exceptions import InvalidConfiguration

_logger = logging.getLogger(__name__)

SCHEME_VANILLA = "mqtt"
SCHEMA_ENCRYPTED = "mqtt+ssl"
DEFAULT_VANILLA_PORT = 1883
DEFAULT_ENCRYPTED_PORT = 8883


class PrintPublisher(object):
    """
    MQTT Print Publisher
    """

    def __init__(self):

        if not BROKER:
            raise InvalidConfiguration(f"Missing entry '{KEY_BROKER}' in [{SECTION_NAME}]")
        if not TOPIC_BASE:
            raise InvalidConfiguration(f"Missing entry '{KEY_TOPIC_BASE}' in [{SECTION_NAME}]")

        self.broker = urlparse(BROKER)
        if self.broker.username and not self.broker.password:
            raise InvalidConfiguration(f"Missing password '{KEY_BROKER}' in [{SECTION_NAME}]")

        if self.broker.scheme == SCHEME_VANILLA:
            self.port = self.broker.port or DEFAULT_VANILLA_PORT
        elif self.broker.scheme == SCHEMA_ENCRYPTED:
            self.port = self.broker.port or DEFAULT_ENCRYPTED_PORT
        else:
            raise InvalidConfiguration(f"Unknown scheme in url '{KEY_BROKER}' in [{SECTION_NAME}]")

    def notify_for_queue(self, dbname, qtoken, job_queues):
        """
        Publish encrypted queue notification

        :param qtoken: remote.mqtt.print.token.queue
        :param job_queues: one or more remote.mqtt.print.job.queue
        """

        def on_connect(client, userdata, flags, reason_code, properties):
            """
            Publish the notifications after a successful connection.
            """
            if reason_code > 0:
                _logger.error(f"Failed connection broker={self.broker.hostname}:{self.port}, code={reason_code}")
                client.disconnect()
                return

            _logger.debug(f"connected mqtt={self.broker.hostname}:{self.port}")
            for job_queue in job_queues:
                public_key = self._read_key(job_queue.public_key)

                payload = {
                    "protocol": PROTOCOL_VERSION,
                    "dbname": dbname,
                    "token": qtoken.token,
                }
                encrypted = public_key.encrypt(
                    bytes(json.dumps(payload), "utf-8"),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None))

                client.publish(job_queue.topic, encrypted)
                _logger.debug(f"published topic={job_queue.topic}, token={qtoken.token}")

            client.disconnect()  # we're done

        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"queue/{dbname}/{str(uuid.uuid4())}")
        if self.broker.username:
            mqtt_client.username_pw_set(self.broker.username, self.broker.password)
        mqtt_client.on_connect = on_connect
        if self.broker.scheme == SCHEMA_ENCRYPTED:
            mqtt_client.tls_set_context(context=ssl.create_default_context())

        mqtt_client.connect(self.broker.hostname, self.port)
        mqtt_client.loop_forever(timeout=10)  # this will disconnect once the notifications have been published

        _logger.debug("mqtt notification done")

    @staticmethod
    def _read_key(path):
        with open(path, "rb") as key_file:
            return serialization.load_pem_public_key(key_file.read(), None)
