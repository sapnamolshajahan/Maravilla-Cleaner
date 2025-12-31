#!/usr/bin/env python3
#
# Remote Print Agent with MQTT
#
# Note that for most part, this is a single-threaded program,
# and message notifications are expected to be processed one-at-a-time.
#
import argparse
import base64
import configparser
import json
import logging
import os
import socket
import ssl
import subprocess
import sys
import tempfile
import uuid
from logging.handlers import TimedRotatingFileHandler
from threading import Lock, Thread
from time import sleep
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from paho.mqtt import client as mqtt
from requests.exceptions import ConnectionError as ReqConnectionError

# Configuration Sections
MAIN_SECTION = "agent"
KEY_BROKER = "broker"
KEY_TOPIC_BASE = "topic_base"
KEY_PRIVATE_KEY = "private_key"
KEY_URLS = "odoo_urls"
KEY_LP_CMD = "lp_command"
KEY_LPSTAT = "lp_status"
KEY_LOG_LEVEL = "log_level"

# Programatic Constants
PROTOCOL_VERSION = "2"  # needs to match publisher's PROTOCOL_VERSION on Odoo
SCHEME_VANILLA = "mqtt"
SCHEME_ENCRYPTED = "mqtt+ssl"
DEFAULT_VANILLA_PORT = 1883
DEFAULT_ENCRYPTED_PORT = 8883
POST_TIMEOUT_MAX = 180  # (seconds) timeout on Odoo conversations
NETWORK_RETRY = 60  # (seconds) retry-sleep on Network Issues
HANDSHAKE_REFRESH = 60 * 60 * 6  # (seconds) handshake refresh with Odoo instances; default to 6 hours
DEFAULT_LP_CMD = "lp -d {queue} -n {copies} -t {name} {path}"
DEFAULT_LPSTAT = "lpstat -e"


def write_pidfile(path):
    try:
        with open(path, "w") as pidfile:
            pidfile.write(f"{os.getpid()}\n")
    except Exception:
        logging.error(f"failed to write pidfile={path}, ignoring", exc_info=True)


def decrypt_payload(private_key, encrypted):
    """
    Unwrap an encrypted payload
    """
    payload_bytes = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None))
    payload = payload_bytes.decode("utf-8")
    return json.loads(payload)


def spool_to_lp(lp_cmd, job):
    """
    Forward data to local print-system
    """
    pathname = False
    try:
        fd, pathname = tempfile.mkstemp(suffix=".remote_print_agent")
        os.write(fd, job.data)
        os.close(fd)

        args = {
            "name": f"remote-job-{job.id}",
            "queue": job.queue,
            "copies": str(job.copies),
            "path": pathname,
        }
        for arg, value in args.items():
            placeholder = "{" + arg + "}"
            lp_cmd = lp_cmd.replace(placeholder, value)
        command = lp_cmd.split()

        logging.debug(f"printing: cmd={command}")
        done = subprocess.run(command, capture_output=True, text=True)
        info = f"printing: exit={done.returncode}"
        if done.stdout:
            info += f", stdout=\"{done.stdout.strip()}\""
        if done.stderr:
            info += f", stderr=\"{done.stderr.strip()}\""
        logging.info(info)

    except Exception:
        logging.error("printing: failed", exc_info=True)

    finally:
        if pathname:
            try:
                os.unlink(pathname)
            except (OSError, IOError):
                pass


class AgentConfig():
    """
    Parse the Configuration file
    """

    def __init__(self, configpath):
        config = configparser.ConfigParser(default_section=MAIN_SECTION, interpolation=None)
        config.read(configpath)

        section = config[MAIN_SECTION]

        # Let's set up logging first, so that log-output can be seen.
        if KEY_LOG_LEVEL in section:
            level = section[KEY_LOG_LEVEL]
            log_level = logging.INFO  # default
            if level == "debug":
                log_level = logging.DEBUG
            elif level == "error":
                log_level = logging.ERROR
            elif level == "warning":
                log_level = logging.WARNING
            logging.getLogger().setLevel(log_level)

        # Mandatory sections
        if KEY_BROKER not in section:
            raise Exception(f"Missing '{KEY_BROKER}' in [{MAIN_SECTION}]")

        self.broker = urlparse(section[KEY_BROKER])
        if self.broker.scheme == SCHEME_VANILLA:
            self.broker_port = self.broker.port or DEFAULT_VANILLA_PORT
        elif self.broker.scheme == SCHEME_ENCRYPTED:
            self.broker_port = self.broker.port or DEFAULT_ENCRYPTED_PORT
        else:
            raise Exception(f"Unknown scheme {self.broker.scheme} in '{KEY_BROKER}' in [{MAIN_SECTION}]")

        self.urls = section[KEY_URLS].split()

        self.lp_cmd = section.get(KEY_LP_CMD, DEFAULT_LP_CMD)
        for keyword in ("copies", "name", "path", "queue"):
            placeholder = "{" + keyword + "}"
            if self.lp_cmd.find(placeholder) < 0:
                raise Exception(f"Missing placeholder {placeholder} for {KEY_LP_CMD}=\"{self.lp_cmd}\"")
        self.lp_status = section.get(KEY_LPSTAT, DEFAULT_LPSTAT)

        with open(section[KEY_PRIVATE_KEY], "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(key_file.read(), None)


class TopicReference():
    """
    Topic domain Properties
    """

    def __init__(self, url: str, queue: str, subscribe: str):
        self.url = url
        self.queue = queue
        self.subscribe = subscribe  # MQTT subscribe message-id


class OdooDbInstance():
    """
    An Odoo db-instance
    """

    def __init__(self, session, url: str):
        self.session = session
        self.url = url
        self._topic_refs = {}  # mqtt-topic: TopicReference

    def add_topic_ref(self, topic: str, ref: TopicReference):
        self._topic_refs[topic] = ref

    def get_topic_ref_by_subscribe(self, message_id) -> TopicReference:
        for _topic, topic_ref in self._topic_refs.items():
            if topic_ref.subscribe == message_id:
                return topic_ref
        return None

    def get_topic_ref_by_topic(self, topic) -> TopicReference:
        return self._topic_refs.get(topic, None)

    def control_topic(self):
        """
        :return: mqtt topic for local control channel
        """
        return f"remote_print_agent/{self.session.session}/{self.url}"

    def setup_control(self):
        """
        Establish local control channel
        """
        control_topic = self.control_topic()
        mqtt_client = self.session.mqtt
        mqtt_client.subscribe(control_topic)
        mqtt_client.message_callback_add(control_topic, self.on_control)
        logging.debug(f"instance control={control_topic}")

    def on_control(self, client, userdata, message):
        """
        Local Control Message
        - there's only one type, which is to re-initiate a handshake.
        """
        logging.info(f"handshake-refresh on {self.url}")
        self.handshake()

    def lpstat(self) -> list[str]:
        """
        Process the output of "lpstat -e" (or equivalent).

        :return: list of queues
        """
        queues = []
        command = self.session.config.lp_status.split()
        done = subprocess.run(command, capture_output=True, text=True)
        if done.stdout:
            queues = done.stdout.strip().split("\n")
        if done.stderr:
            logging.error(f"stderr={done.stderr.strip()}")
        return queues

    def handshake(self):
        """
        Initiate conversation with Odoo.
        """
        config = self.session.config

        # Disconnect all queue topics
        for topic in self._topic_refs.keys():
            self.session.mqtt.unsubscribe(topic)
        self._topic_refs = {}

        while self.session.mqtt_connected():
            try:
                queues = self.lpstat()
                logging.debug(f"print-queues={queues}")
                odoo = OdooClient(self.url, None)
                result = odoo.submit_info(self.session.name, queues,
                                          self.session.session, self.session.session_signature)
                if result and "topics" in result:
                    for queue in queues:
                        q_topic = result["topics"][queue]
                        _success, m_id = self.session.mqtt.subscribe(f"{q_topic}")
                        self.add_topic_ref(q_topic, TopicReference(self.url, queue, m_id))
                        logging.debug(f"queue={queue}, subscribe={q_topic}")

                    logging.info(f"configured domain={self.url}")
                    Thread(target=self.refresh_handshake).start()
                    return

                logging.error(f"configure domain={self.url} has unexpected result={result}, retry in {NETWORK_RETRY}s")

            except Exception as e:
                logging.error(f"configure failed domain={self.url}, retry in {NETWORK_RETRY}s; exception={e}")
            sleep(NETWORK_RETRY)

    def refresh_handshake(self):
        """
        Re-initiate a handshake after waiting for a while.
        This is expected to be run in a separate Thread.
        """
        sleep(HANDSHAKE_REFRESH)

        # Don't attempt to call self.handshake() while on a separate Thread(), as
        # it will interfere with mqtt-paho message-dispatch.
        # Initiate a refresh by dropping a message onto the control channel.
        self.session.mqtt.publish(self.control_topic(), "refresh-request")


class RemoteJob():

    def __init__(self, raw):
        self.id = raw.get("id", 0)  # TODO: remove once all Odoo-instances have been upgraded
        self.queue = raw["queue"]
        self.copies = raw.get("copies", 1)  # TODO: remove once all Odoo-instances have been upgraded
        self.data = base64.b64decode(raw["data"])

    def __str__(self):
        return f"{{id={self.id}, queue={self.queue}, copies={self.copies}}}"


class OdooClient():
    """
    Conversations with an Odoo instance
    """

    def __init__(self, url: str, dbname: str):
        self.url = url
        self.dbname = dbname

    def _post_odoo(self, entry, params):
        """
        Post to Odoo
        """
        json_rpc = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "search",
            "params": params,
        }
        endpoint = f"{self.url}/remote_print_mqtt/{entry}"
        if self.dbname:
            endpoint += "/" + self.dbname

        headers = {
            "Content-Type": "application/json",
        }
        data = json.dumps(json_rpc)
        logging.debug(f"post url={endpoint}, params={params}")
        response = requests.post(endpoint, data=data, headers=headers, timeout=POST_TIMEOUT_MAX)
        if response.status_code not in [200, 201, 202]:
            logging.error(f"invalid response endpoint={endpoint}, code={response.status_code}")
            return {}

        json_response = response.json()
        if "error" in json_response:
            error = json_response["error"]
            if "data" in error and "message" in error["data"]:
                message = error["data"]["message"]
                logging.error(f"remote error-message={message}")
            return {}

        return json_response["result"]

    def submit_info(self, hostname, queues, channel, signature: bytes):
        return self._post_odoo(
            "remote-info",
            {
                "hostname": hostname,
                "queues": queues,
                "channel": channel,
                "signature": base64.b64encode(signature).decode("utf-8"),
            })

    def ask_token(self, queue):
        """
        Ask for token
        """
        return self._post_odoo("token", {"queue": queue})

    def ls_queue(self, token):
        """
        List jobs in queue with token
        """
        return self._post_odoo("list", {"token": token})

    def get_job(self, token) -> RemoteJob:
        """
        Get Job data from Odoo
        """
        response = self._post_odoo("job", {"token": token})
        if "data" not in response:
            logging.error("remote-error: 'data' not found?")
            return None
        return RemoteJob(response)


class AgentSession():
    """
    A running Agent
    """

    def __init__(self, config: AgentConfig):
        self.name = socket.gethostname()
        self.config = config
        self.session = str(uuid.uuid4())

        # MQTT session names need to be semi-random to allow repeated re-connections
        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"print/{self.name}/{self.session}",
                                clean_session=True)
        if config.broker.username:
            self.mqtt.username_pw_set(config.broker.username, config.broker.password)
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_subscribe = self.on_subscribe
        self.mqtt.on_message = self.on_message
        if config.broker.scheme == SCHEME_ENCRYPTED:
            self.mqtt.tls_set_context(context=ssl.create_default_context())

        # Sign the session
        self.session_signature = self.config.private_key.sign(
            bytes(self.session, "utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256())

        # The following data should only be manipulated with a thread-lock after start()
        self.data_lock = Lock()
        self.connected = False  # use with data_lock
        self._instances = [OdooDbInstance(self, url) for url in config.urls]

    def get_topic_ref_by_subscribe(self, message_id) -> TopicReference:
        with self.data_lock:
            for instance in self._instances:
                topic_ref = instance.get_topic_ref_by_subscribe(message_id)
                if topic_ref:
                    return topic_ref
        return None

    def get_topic_ref_by_topic(self, topic) -> TopicReference:
        with self.data_lock:
            for i in self._instances:
                topic_ref = i.get_topic_ref_by_topic(topic)
                if topic_ref:
                    return topic_ref
        return None

    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code > 0:
            logging.error(f"failed to connect, code={reason_code}, broker={self.config.broker.hostname}")
            return
        logging.info(f"connected broker={self.config.broker.hostname}:{self.config.broker_port}")

        with self.data_lock:
            self.connected = True
            for instance in self._instances:
                instance.setup_control()
                Thread(target=instance.handshake).start()

    def on_disconnect(self, client, userdata, flags, reason_code, properties):

        logging.info(f"disconnected broker={self.config.broker.hostname}:{self.config.broker_port}")
        with self.data_lock:
            self.connected = False

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        """
        Ask Odoo for queue-tokens on startup, to clear outstanding jobs.
        """
        topic_ref = self.get_topic_ref_by_subscribe(mid)
        if not topic_ref:
            logging.debug(f"ignore non-queue subscription")
            return

        odoo = OdooClient(topic_ref.url, None)
        try:
            logging.debug(f"ask-token: domain={topic_ref.url}, queue={topic_ref.queue}")
            odoo.ask_token(topic_ref.queue)
        except ReqConnectionError as e:
            # Generally caused by network failure, or dead Odoo server.
            # Can be ignored, as new jobs will wake up the queue
            logging.error(f"Odoo failure: domain={topic_ref.url}, exception={e}, skipping")

    def on_message(self, client, userdata, message):
        """
        Process a queue-notification
        """
        try:
            payload = decrypt_payload(self.config.private_key, message.payload)

            if "protocol" not in payload:
                logging.error(f"protocol version not in payload")
                return
            if payload["protocol"] != PROTOCOL_VERSION:
                logging.error(f"internal-error: expected protocol={PROTOCOL_VERSION}")
                return

            dbname = payload["dbname"]
            token = payload["token"]

        except Exception:
            logging.error("failed to unpack payload", exc_info=True)
            return

        topic_ref = self.get_topic_ref_by_topic(message.topic)
        if not topic_ref:
            logging.error(f"no local-reference found for topic={message.topic}")
            return

        logging.debug(f"notification: domain={topic_ref.url}, queue={topic_ref.queue}, dbname={dbname}, token={token}")

        try:
            client = OdooClient(topic_ref.url, dbname)
            result = client.ls_queue(token)
            if "jobs" not in result:
                logging.error("remote-error: 'jobs' not found?")
                return

            job_tokens = result["jobs"]
            if not job_tokens:
                logging.info(f"no jobs on url={topic_ref.url}, queue={topic_ref.queue}, dbname={dbname}")
                return

            for job_token in job_tokens:
                job = client.get_job(job_token)
                if not job:
                    continue

                logging.info(
                    f"received job: domain={topic_ref.url}, token={job_token}, "
                    f"dbname={dbname}, job={job}, {len(job.data)} bytes")
                spool_to_lp(self.config.lp_cmd, job)

        except ReqConnectionError as e:
            logging.error(f"Odoo failure: domain={topic_ref.url}, exception={e}")

    def start(self):
        while True:
            try:
                self.mqtt.connect(self.config.broker.hostname, self.config.broker_port)
                self.mqtt.loop_forever()

            except socket.gaierror as e:
                # Possible causes:
                # - Network down
                # - hostname incorrect
                logging.error("Local network?: "
                              f"host={self.config.broker.hostname}, exception={e}, retry in {NETWORK_RETRY}s")

            except ConnectionError as e:
                # Errors at this point are likely due to remote MQTT server issues
                logging.error("MQTT server?: "
                              f"host={self.config.broker.hostname}, exception={e}, retry in {NETWORK_RETRY}s")
                try:
                    self.mqtt.disconnect()
                except Exception:
                    pass

            except Exception as e:
                # Yeah, not quite the best thing to do; but there are a lot of unusual system-env exceptions...
                logging.error(f"Unexpected error: exception={e}, retry in {NETWORK_RETRY}s")

            sleep(NETWORK_RETRY)

    def mqtt_connected(self):
        # lock required for protected data...
        with self.data_lock:
            return self.connected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-pid", help="PID file, if specified")
    parser.add_argument("-log", help="log file, if specified")
    parser.add_argument("config", help="client configuration file")
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        print(f"ERROR: missing configuration file '{args.config}'")
        exit(1)

    if args.pid:
        write_pidfile(args.pid)

    # Set up logging first
    handler = None
    if args.log:
        logdir = os.path.dirname(args.log)
        if logdir and os.path.isdir(logdir):
            logfile = os.path.basename(args.log)
            handler = TimedRotatingFileHandler(args.log, when="W6", backupCount=9)
    if not handler:
        handler = logging.StreamHandler(stream=sys.stdout)  # fallback
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO, handlers=[handler])

    agent = AgentSession(AgentConfig(args.config))
    agent.start()
