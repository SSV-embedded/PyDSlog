
# Usage MLS/160A with Docker

## Dependencies
* Docker basics: https://docs.docker.com/
* Docker CLI: https://docs.docker.com/engine/reference/commandline/docker/
* Node-RED basics: https://nodered.org/docs/
* Linux OS basics
* Computer (RMG/938, RaspberryPi, Debian Linux PC) with USB or serial port
* MLS/160A with USB or serial plug

## Installing Docker
In case the Docker engine is not installed yet, here are some short instructions:
- How to install Docker on RMG/938
	```
	apt-get update && apt-get upgrade
	apt-get install ca-certificates docker-ce
	apt-get install rmg938-app-docker
	```

- How to install Docker on a RaspberryPi or Debian
	```
	sudo apt-get update && sudo apt-get upgrade
	sudo apt-get install -y apt-transport-https ca-certificates
	curl -sSL https://get.docker.com | sh
	```
	Add user to the docker group (assume user `pi`)
	```
	sudo usermod -aG docker pi
	```
	For the changes to happen, you need to log out and then back in again.

- How to install Docker Compose on a RaspberryPi or Debian
	```
	sudo apt-get install -y libffi-dev libssl-dev python3 python3-pip
	sudo pip3 -v install docker-compose
	```

## Download docker images
```
docker pull eclipse-mosquitto:openssl
docker pull ssvembeddedde/pydslog2mqtt:0.1.0
docker pull nodered/node-red:latest
```

## Create configuration
Create minimal configuration for MQTT broker and data directory for Node-RED.
- On RMG/938 we take `/media/data` as directory:
	```
	WORK_DIR=/media/data
	```
- On RaspberryPi or Debian we take `~/work` as work directory in this example.
	```
	WORK_DIR=~/work
	```
Create work directories and the Mosquitto minimal configuration
```
mkdir -p $WORK_DIR/tt_mosquitto $WORK_DIR/tt_nodered
cat > $WORK_DIR/tt_mosquitto/mosquitto.conf <<EOF
persistence false
allow_anonymous true
log_dest none
listener 1883
EOF
```

## Start containers with docker-compose
- Create docker-compose file
```
cat > ~/work/docker-compose.yaml <<-EOF
version: "3.9"
services:
  mosquitto:
    image: eclipse-mosquitto:openssl
    ports:
      - 1883:1883
    volumes:
      - ~/work/tt_mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf
    restart: unless-stopped
  pydslog2mqtt:
    image: ssvembeddedde/pydslog2mqtt:0.1.0
    devices:
      - "/dev/ttyUSB0:/dev/ttyS0"
    environment:
      - MQTT_URL=mqtt://mosquitto:1883
    restart: unless-stopped
  nodered:
    image: nodered/node-red:latest
    ports:
      - 1880:1880
    volumes:
      - ~/work/tt_nodered:/data
    restart: unless-stopped
EOF
```

- Start docker
```
docker-compose up -d
```

## Start all containers manually
- Start Mosquitto container
	```
	docker run -d -p 1883:1883 -v $WORK_DIR/tt_mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf --restart=unless-stopped --name tt_mosquitto eclipse-mosquitto:openssl
	```
- Start pydslog2mqtt
	- Find the MQTT broker IP
	```
	docker inspect tt_mosquitto | grep "IPAddress"
	```
	- Find the serial port to which the sensor is connected to (here, it is /dev/ttyS2) and start the container
	```
	docker run -d --restart=unless-stopped --name tt_pydslog2mqtt --device /dev/ttyS2:/dev/ttyS0 -e "MQTT_URL=172.17.0.2:1883" ssvembeddedde/pydslog2mqtt:0.1.0
	```

- Start the Node-RED Docker
	```
	docker run -d -p 1880:1880 -v $WORK_DIR/tt_nodered:/data --restart=unless-stopped --name tt_nodered nodered/node-red:latest
	```

## Use sensor
- Open installed Node-RED: **http://***device-ip***:1880**
- Inside Node-RED open `Menu` > `Manage palette` search and install node `node-red-contrib-pydslog2mqtt`
- Import this example flow to Node-RED:
```
[{"id":"efda7b2a.7aeec8","type":"pydslog","z":"32efee25.3783c2","name":"","topic":"","device":"mls160a","freq":512,"channels":["ACCX","ACCY","ACCZ"],"broker":"b77e05b.0db3bf8","x":480,"y":80,"wires":[["f986f0c5.4ddac"]]},{"id":"6d8ce15f.9c41c","type":"inject","z":"32efee25.3783c2","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"","crontab":"","once":false,"onceDelay":0.1,"topic":"","payload":"start","payloadType":"str","x":270,"y":80,"wires":[["efda7b2a.7aeec8"]]},{"id":"a4f5f5c9.b15b18","type":"inject","z":"32efee25.3783c2","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"","crontab":"","once":false,"onceDelay":0.1,"topic":"","payload":"stop","payloadType":"str","x":270,"y":140,"wires":[["efda7b2a.7aeec8"]]},{"id":"f986f0c5.4ddac","type":"debug","z":"32efee25.3783c2","name":"","active":false,"tosidebar":true,"console":false,"tostatus":false,"complete":"false","statusVal":"","statusType":"auto","x":670,"y":120,"wires":[]},{"id":"b77e05b.0db3bf8","type":"mqtt-broker","name":"","broker":"172.17.0.2","port":"1883","clientid":"","usetls":false,"compatmode":false,"keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","closeTopic":"","closeQos":"0","closePayload":"","willTopic":"","willQos":"0","willPayload":""}]
```
