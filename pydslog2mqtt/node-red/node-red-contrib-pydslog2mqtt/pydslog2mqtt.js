/**
 * Copyright 2016 SSV Software Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/

module.exports = function(RED) {
    "use strict";
    function pydslogNode(n) {
        RED.nodes.createNode(this,n);
        this.device = n.device;
        this.channels = n.channels;
        this.qos = 1;
        this.freq = n.freq;
        this.topic = n.topic || 'pydslog';
        this.broker = n.broker;
        this.brokerConn = RED.nodes.getNode(this.broker);
        this.config = {
            conf: {
                in: {
                    device: this.device,
                    channels: this.channels,
                    freq: this.freq,
                    frameSize: this.freq
                },
                out: {
                    data: "raw"
                }
            },
            job: "stop"
        }
        this.topic_val = this.topic + '/v';
        this.topic_conf = this.topic + '/C';
        this.topic_stat = this.topic + '/S';
        
        var node = this;

        if (this.brokerConn) {
            this.status({fill:"red", shape:"ring", text:"disconnected"});
            node.brokerConn.register(this);

            this.brokerConn.subscribe(this.topic_stat, this.qos, function(topic, payload, packet) {
                payload = payload.toString();
                if(payload == "0") {
                    node.status({fill:"red", shape:"ring", text:"disconnected"});
                } else if (payload == "1") {
                    node.status({fill:"yellow", shape:"dot", text:"connected"});
                } else if (payload == "2") {
                    node.status({fill:"green", shape:"dot", text:"streaming"});
                }
            }, this.id);

            this.brokerConn.subscribe(this.topic_val, this.qos, function(topic, payload, packet) {
                payload = JSON.parse(payload.toString());
                node.send({payload: payload});
            }, this.id);

            this.on("input", function(msg){
                var payload = msg.payload.toString();
                if(payload == "start") {
                    node.config.job = "start";
                } else if(payload == "stop") {
                    node.config.job = "stop";
                } else {
                    return;
                }
                var message = {
                    topic: node.topic_conf,
                    payload: node.config
                }
                node.brokerConn.publish(message);
            });
        } else {
            this.error("Missing broker configuration");
        }

        this.on('close', function(removed, done) {
            if (node.brokerConn) {
                node.brokerConn.unsubscribe(node.topic_stat, node.id, removed);
                node.brokerConn.unsubscribe(node.topic_val, node.id, removed);
                node.brokerConn.deregister(node, done);
            }
        });
    }
    RED.nodes.registerType("pydslog", pydslogNode);
};
