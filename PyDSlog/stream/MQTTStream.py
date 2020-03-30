"""
  ____          ____   ____   _                         ____  ____ __     __ 
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / / 
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /  
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V / 
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/ 
         |___/                          |___/                     

"""

import paho.mqtt.client as mqtt
from collections import OrderedDict
import ipaddress
import queue
import json 

class MQTT_stream:
    
    def __init__(self, topic, mqtt_ip, mqtt_port, channels_to_use, json_index="payload", mqtt_client_id="", keepalive=60):
        
        self.topic              = topic
        self.mqtt_ip            = mqtt_ip
        self.mqtt_client_id     = mqtt_client_id
        self.keepalive          = keepalive
        self.channels_to_use    = channels_to_use
        self.json_index         = json_index
        
        try:
            self.mqtt_port          = int(mqtt_port)
            ipaddress.ip_address(self.mqtt_ip)
        except Exception as e:
            raise e
            
        if(self.json_index == ""):
            raise ValueError("JSON index not defined")
            
        if(self.topic == ""):
            raise ValueError("topic not defined")

        if(self.channels_to_use[0] == ""):
            raise ValueError("JSON keys not defined")

        
        self.stream_values = queue.Queue(0) 
        
        self.client_mqtt_data              = mqtt.Client(client_id=self.mqtt_client_id, clean_session=True)
        self.client_mqtt_data.on_connect   = self.on_connect
        self.client_mqtt_data.on_message   = self.on_message


    def on_connect(self, client, userdata, flags, rc):   # subscribe to "run_folder"

        client.subscribe(self.topic, qos=0)

    def on_message(self, client, userdata, msg):

        if(msg.topic == self.topic):
            v = msg.payload.decode("utf-8")
            self.stream_values.put(v)


    def start(self):

        self.client_mqtt_data.connect(self.mqtt_ip, self.mqtt_port, self.keepalive)
        self.client_mqtt_data.loop_start()


    def stop(self): # Stop the loops

        self.client_mqtt_data.disconnect()
        self.client_mqtt_data.loop_stop()

    def values_waiting_in_MQTT_stream(self): 
        
        if(self.stream_values.empty()):            
            return False
        else:  
            return True
     

    def read(self, transpose=False): 
    
        try:

            no_values = 1
            while(no_values):

                try:
                    v = self.stream_values.get(block=False)                        # read queue  / non blocking
                except queue.Empty:
                    no_values = 1
                else:   
                    v = (json.loads(v, object_pairs_hook=OrderedDict))
                    
                    l = []
                    for key, values in v[self.json_index].items():
                        for c in self.channels_to_use:
                            if(c == key):
                                if(transpose):

                                    if (isinstance(values, list) == False):
                                        values = [values]

                                    if (len(l) == 0):
                                        l = [[] for j in range(0, len(values))]
                                    for n in range(0, len(values)):
                                        l[n].append(values[n])

                                else:

                                    if (isinstance(values, list) == False):
                                        values = [values]

                                    l.append(values)

                    no_values = 0   
                    
            return l
            
        except Exception as e:
            raise e
