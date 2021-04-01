#!/usr/bin/env python3
"""
"""

import paho.mqtt.client as mqtt
import PyDSlog.stream as stream
import time
from datetime import datetime
import json

import os
import sys
import logging
import logging.handlers
import signal

VERSION = '1.0.0'
PROGRAM = 'pydslog2mqtt'

CONFIG_TMP = None
CONFIG = None
BACKEND = None

is_streaming = False
is_connected = False
is_error = ""

flag_reconfigure = False
flag_start = False
flag_stop = False


TOPIC_DATA = '/v'
TOPIC_ERROR = '/E'
TOPIC_CONFIG = '/C'
TOPIC_STATUS = '/S'

logger = logging.getLogger('')
Grun = 5

def signal_handler(signal, frame):
    global Grun
    logger.debug("Caught signal, shutting down...")
    Grun = 0

def set_error(msg=None):
    global is_error
    if msg == None:
        is_error = ""
    else:
        is_error = str(msg)

def on_subscribe(mqttc, obj, mid, granted_qos):
    logger.debug("MQTT: subscribed topic '%s'", TOPIC_CONFIG)

def on_unsubscribe(mqttc, obj, mid):
    logger.debug("MQTT: unsubscribed topic '%s'", TOPIC_CONFIG)

def on_connect(mqttc, obj, flags, rc):
    global is_connected
    if rc == 0:
        logger.debug("MQTT: connection successful")
        mqttc.subscribe(TOPIC_CONFIG)
        mqttc.publish(TOPIC_STATUS, "1", retain=True)
        is_connected = True
    elif rc == 1:
        logger.error("MQTT: connection refused - incorrect protocol version")
    elif rc == 2:
        logger.error("MQTT: connection refused - invalid client identifier")
    elif rc == 3:
        logger.error("MQTT: connection refused - server unavailable")
    elif rc == 4:
        logger.error("MQTT: connection refused - bad username or password")
    elif rc == 5:
        logger.error("MQTT: connection refused - not authorised")
    else:
        logger.error("MQTT: connection failed ({0})".format(rc))

def on_disconnect(mqttc, obj, rc):
    global is_connected
    logger.debug("MQTT: disconnect ({0})".format(rc))
    is_connected = False

def on_message(mqttc, obj, msg):
    global CONFIG_TMP
    global flag_reconfigure
    global flag_start
    global flag_stop

    logger.debug("MQTT: message topic {0} {1}".format(msg.topic, msg.payload))
    try:
        v = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        set_error('json syntax error')
        return

    if "conf" in v:
        config = parse_config(v["conf"])
        if config != None and config != CONFIG:
            CONFIG_TMP = config
            flag_reconfigure = True
            logger.debug("PDSL: got configuration")

    if "job" in v:
        j = v["job"]
        if j == "start":
            flag_start = True
            logger.debug("PDSL: got command start")
        if j == "stop":
            flag_stop = True
            logger.debug("PDSL: got command stop")

def parse_config(c):
    logger.debug("PDSL: parse configuration")
    if type(c) is not dict:
        set_error("attribute 'conf' is empty")
        return None

    for i in ["in","out"]:
        if i not in c:
            set_error("missing attribute 'conf."+i+"'")
            return None

    c_in = c["in"]
    c_out = c["out"]
    for i in  ["device","channels","freq","frameSize"]:
        if i not in c_in:
            set_error("missing attribute 'conf.in."+i+"'")
            return None

    if "data" not in c_out:
        set_error("missing attribute 'conf.out.data'")
        return None

    if c_in["device"] not in {"mls160a", "io5640"}:
        set_error("unsupported device '"+c_in["device"]+"'")
        return None

    # TODO test chennels freq size
    return c

def pdsl_restart():
    global BACKEND
    global CONFIG
    global FFT
    global flag_start
    global flag_stop
    global flag_reconfigure
    global is_streaming

    logger.debug("PDSL: reconfigure")

    port="/dev/ttyS0"
    baudrate=115200
    CONFIG = CONFIG_TMP

    if BACKEND != None and is_streaming and (flag_reconfigure or flag_stop):
        BACKEND.stop()
        BACKEND.disconnect()
        is_streaming = False
        mqttc.publish(TOPIC_STATUS, "1", retain=True)
        logger.debug("PDSL: stop streaming")

    if flag_reconfigure:
        if(CONFIG["in"]["device"]  == "mls160a"):
            BACKEND = stream.MLS160A_stream(
                sz_block=CONFIG["in"]["frameSize"], 
                channels_to_use=CONFIG["in"]["channels"], 
                frequency=CONFIG["in"]["freq"], 
                port=port, baudrate=baudrate)

        elif(CONFIG["in"]["device"]  == "io5640"):
            BACKEND = stream.IO5640_stream(
                sz_block=CONFIG["in"]["frameSize"], 
                channels_to_use=CONFIG["in"]["channels"], 
                frequency=CONFIG["in"]["freq"], 
                port=port, baudrate=baudrate)

        if(CONFIG["out"]["data"] == "fft"):
            freq = CONFIG["in"]["freq"]
            signlen = CONFIG["in"]["frameSize"]
            period = 1.0/freq
            FFT = fft.FFTGenerator(period, signlen, freq)

        logger.debug("PDSL: create streamer '"+CONFIG["in"]["device"]+"'")

    if BACKEND != None and not is_streaming and flag_start:
        BACKEND.connect()
        BACKEND.start()
        is_streaming = True
        mqttc.publish(TOPIC_STATUS, "2", retain=True)
        logger.debug("PDSL: start streaming")

    # reset all flags
    flag_reconfigure = False
    flag_stop = False
    flag_start = False

if __name__ == "__main__":
    loglevel = logging.INFO
    std_handler = logging.StreamHandler(stream=sys.stdout)
    std_formatter = logging.Formatter("%(filename)s %(asctime)s - %(levelname)s - %(message)s")
    std_handler.setFormatter(std_formatter)
    try:
        loglevel = int(os.getenv('LOGLEVEL', logging.INFO))
        # https://docs.python.org/3/library/logging.html#levels
    except Exception as e:
        loglevel = logging.INFO
        pass
    logger.addHandler(std_handler)
    logger.setLevel(loglevel)

    logger.info("Starting %s v%s", PROGRAM, VERSION)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # get config
    mqttc = mqtt.Client()
    try:
        tmp = os.getenv('MQTT_URL')
        if not tmp:
            raise Exception("no MQTT_URL environment set")
        tmp = tmp.split('/')
        if len(tmp) > 1:
            tmp = tmp[2].split(':')
        else:
            tmp = tmp[0].split(':')
        mqhost = tmp[0]
        if len(tmp) > 1:
            mqport = int(tmp[1])
        else:
            mqport = 1883
        user = os.getenv('MQTT_USER')
        passwd = os.getenv('MQTT_PASS')
        prefix = os.getenv('MQTT_BASE_TOPIC', 'pydslog')
        TOPIC_DATA = prefix + TOPIC_DATA
        TOPIC_ERROR = prefix + TOPIC_ERROR
        TOPIC_CONFIG = prefix + TOPIC_CONFIG
        TOPIC_STATUS = prefix + TOPIC_STATUS

        logger.info("CONF: broker address: %s", mqhost)
        logger.info("CONF: broker port: %d", mqport)
        logger.info("CONF: broker user: %s", user)
        logger.info("CONF: broker pass: %s", passwd)
        logger.info("CONF: topic data: %s", TOPIC_DATA)
        logger.info("CONF: topic error: %s", TOPIC_ERROR)
        logger.info("CONF: topic config: %s", TOPIC_CONFIG)
        logger.info("CONF: topic status: %s", TOPIC_STATUS)

        mqttc.on_connect = on_connect
        mqttc.on_message = on_message
        mqttc.on_subscribe = on_subscribe
        mqttc.on_unsubscribe = on_unsubscribe
        mqttc.will_set(TOPIC_STATUS, "0", retain=True)
        if user and passwd:
            mqttc.username_pw_set(username=user, password=passwd)

        logger.info("MQTT: connect to mqtt %s:%s broker.", mqhost, mqport)
        mqttc.connect(mqhost, mqport, 60)
        mqttc.loop_start()

    except Exception as e:
        logger.exception(e)
        logger.error(e)
        exit(1)

    try:
        logger.info("Running...")
        while Grun > 0:
            if is_connected:
                if flag_reconfigure or flag_stop or flag_start:
                    pdsl_restart()
                if is_error:
                    mqttc.publish(TOPIC_ERROR, json.dumps({'error':str(is_error)}), retain=False)
                    set_error()
                if is_streaming:
                    v = BACKEND.read(transpose=False)
                    data = {
                        "time": datetime.now().replace(microsecond=0).isoformat(),
                        "data": {}
                    }
                    for i in range(0,len(CONFIG["in"]["channels"])):
                        data["data"].update({str(CONFIG["in"]["channels"][i]):v[i]})
                    mqttc.publish(TOPIC_DATA, json.dumps(data), retain=False)
                    continue

            time.sleep(1)

        mqttc.unsubscribe(TOPIC_CONFIG)
        if is_streaming:
            BACKEND.stop()
            BACKEND.disconnect()
        mqttc.publish(TOPIC_STATUS, "0", retain=True)
        mqttc.loop_stop()

    except Exception as e:
        logger.exception(e)
        pass

    logger.info("Stopped")
