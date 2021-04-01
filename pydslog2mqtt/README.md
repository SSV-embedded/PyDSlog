
# Usage MLS/160A with Docker

## Install on RMG/938
- HowTo install docker on RMG/938
	```
	apt update
	apt install ca-certificates docker-ce
	apt install rmg938-app-docker
	```

- Download docker images
	```
	docker pull eclipse-mosquitto:openssl
	docker pull ssvembeddedde/pydslog2mqtt:0.1.0
	docker pull nodered/node-red:latest
	```

- Start MQTT broker
	```
	mkdir -m 777 /media/data/tt_mosquitto
	cat > /media/data/tt_mosquitto/mosquitto.conf <<EOF
	persistence false
	allow_anonymous true
	log_dest none
	listener 1883
	EOF

	docker run -d -p 1883:1883 -v /media/data/tt_mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf --name tt_mosquitto eclipse-mosquitto:openssl
	```

- Start pydslog2mqtt
	- Find MQTT broker ip
	```
	docker inspect tt_mosquitto | grep "IPAddress"
	```
	- Find serial port where sensor is connected to (here /dev/ttyS2) and start container
	```
	docker run -d --name tt_pydslog2mqtt --device /dev/ttyS2:/dev/ttyS0 -e "MQTT_URL=172.17.0.2:1883" ssvembeddedde/pydslog2mqtt:0.1.0
	```

- Start Node-RED docker
	```
	mkdir -m 777 /media/data/tt_nodered

	docker run -d -p 1880:1880 -v /media/data/tt_nodered:/data --name tt_nodered nodered/node-red:latest
	```

## Install on RaspberryPi, Linux
### HowTo install docker
	https://phoenixnap.com/kb/docker-on-raspberry-pi

### Start manualy
- Download docker images
	```
	docker pull eclipse-mosquitto:openssl
	docker pull ssvembeddedde/pydslog2mqtt:0.1.0
	docker pull nodered/node-red:latest
	```

- Start MQTT broker
	- Create a simple mosquitto configuration and start container
	```
	mkdir -m 777 ~/work/tt_mosquitto
	cat > ~/work/tt_mosquitto/mosquitto.conf <<EOF
	persistence false
	allow_anonymous true
	log_dest none
	listener 1883
	EOF

	docker run -d -p 1883:1883 -v ~/work/tt_mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf --name tt_mosquitto eclipse-mosquitto:openssl
	```

- Start pydslog2mqtt
	- Find MQTT broker ip
	```
	docker inspect tt_mosquitto | grep "IPAddress"
	```
	- Find serial port where sensor is connected to (here /dev/ttyUSB0) and start container
	```
	docker run -d --name tt_pydslog2mqtt --device /dev/ttyUSB0:/dev/ttyS0 -e "MQTT_URL=172.17.0.2:1883" ssvembeddedde/pydslog2mqtt:0.1.0
	```

- Start Node-RED docker
	```
	mkdir -m 777 ~/work/tt_mosquitto/tt_nodered

	docker run -d -p 1880:1880 -v ~/work/tt_mosquitto/tt_nodered:/data --name tt_nodered nodered/node-red:latest
	```

### Start with docker-compose
ToDo

## Use sensor
- Open installed Node-RED
- Install over `Manage palette` `node-red-contrib-pydslog2mqtt` node
- Example flow to use:
```
[{"id":"efda7b2a.7aeec8","type":"pydslog","z":"32efee25.3783c2","name":"","topic":"","device":"mls160a","freq":512,"channels":["ACCX","ACCY","ACCZ"],"broker":"b77e05b.0db3bf8","x":480,"y":80,"wires":[["f986f0c5.4ddac"]]},{"id":"6d8ce15f.9c41c","type":"inject","z":"32efee25.3783c2","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"","crontab":"","once":false,"onceDelay":0.1,"topic":"","payload":"start","payloadType":"str","x":270,"y":80,"wires":[["efda7b2a.7aeec8"]]},{"id":"a4f5f5c9.b15b18","type":"inject","z":"32efee25.3783c2","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"","crontab":"","once":false,"onceDelay":0.1,"topic":"","payload":"stop","payloadType":"str","x":270,"y":140,"wires":[["efda7b2a.7aeec8"]]},{"id":"f986f0c5.4ddac","type":"debug","z":"32efee25.3783c2","name":"","active":false,"tosidebar":true,"console":false,"tostatus":false,"complete":"false","statusVal":"","statusType":"auto","x":670,"y":120,"wires":[]},{"id":"b77e05b.0db3bf8","type":"mqtt-broker","name":"","broker":"172.17.0.2","port":"1883","clientid":"","usetls":false,"compatmode":false,"keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","closeTopic":"","closeQos":"0","closePayload":"","willTopic":"","willQos":"0","willPayload":""}]
```
