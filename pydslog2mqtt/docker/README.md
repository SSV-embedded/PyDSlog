# Docker image for pydslog2mqtt service

Supported architectures armv7, amd64

# Usage
## Pull and run
```
docker pull ssvembeddedde/pydslog2mqtt:0.1.0

docker run -d --restart unless-stopped --name pydslog2mqtt --device /dev/ttyUSB4:/dev/ttyS0 -e "MQTT_URL=192.168.0.119:1883" ssvembeddedde/pydslog2mqtt:0.1.0
```

### Parameter
* The serial port to which the MLS160A or IO/5640-SD is connected to should be bound to the internal device /dev/ttyS0:
	```
	--device /dev/ttyUSB4:/dev/ttyS0
	```

* Configurate the MQTT broker settings with environment variables
	* Broker addresse and port (port is optional, the default is 1883)
	```
	-e "MQTT_URL=192.168.0.119:1883"
	```
	* Broker credentials (optional):
	```
	-e "MQTT_USER=user"
	-e "MQTT_PASS=pass"
	```
	* Base Topic (optional, the default is `pydslog`):
	```
	-e "MQTT_BASE_TOPIC=mls160a/0"
	```

# Build
## How to do multi-platform building
Create buildx and builder
```
export DOCKER_BUILDKIT=1
docker build --platform=local -o . git://github.com/docker/buildx
mkdir -p ~/.docker/cli-plugins
mv buildx ~/.docker/cli-plugins/docker-buildx

docker run --privileged --rm tonistiigi/binfmt --install all

docker buildx create --use --name mybuilder
docker buildx use mybuilder
docker buildx inspect --bootstrap
docker buildx ls
```
Info:
* https://community.arm.com/developer/tools-software/tools/b/tools-software-ides-blog/posts/getting-started-with-docker-for-arm-on-linux
* https://github.com/docker/buildx#building-multi-platform-images


## Build and test local
```
./build.sh dev 0.1.0

docker run -it --rm --name pydslog2mqtt_0 --device /dev/zero:/dev/ttyS0 -e "MQTT_URL=test.mosquitto.org:1883" ssvembeddedde/pydslog2mqtt:0.1.0

pydslog2mqtt.py 2021-03-30 11:21:23,476 - INFO - Starting pydslog2mqtt v1.0.0
pydslog2mqtt.py 2021-03-30 11:21:23,477 - INFO - CONF: broker address: test.mosquitto.org
pydslog2mqtt.py 2021-03-30 11:21:23,477 - INFO - CONF: broker port: 1883
pydslog2mqtt.py 2021-03-30 11:21:23,478 - INFO - CONF: broker user: None
pydslog2mqtt.py 2021-03-30 11:21:23,478 - INFO - CONF: broker pass: None
pydslog2mqtt.py 2021-03-30 11:21:23,479 - INFO - CONF: topic data: pydslog/v
pydslog2mqtt.py 2021-03-30 11:21:23,479 - INFO - CONF: topic error: pydslog/E
pydslog2mqtt.py 2021-03-30 11:21:23,480 - INFO - CONF: topic config: pydslog/C
pydslog2mqtt.py 2021-03-30 11:21:23,480 - INFO - CONF: topic status: pydslog/S
pydslog2mqtt.py 2021-03-30 11:21:23,480 - INFO - MQTT: connect to mqtt test.mosquitto.org:1883 broker.
pydslog2mqtt.py 2021-03-30 11:21:23,537 - INFO - Running...
```

## Build multi-platform release and upload
Build and push for amd64 and armv7
```
./build.sh del 0.1.0
```

## Build to tar
The multi-platform image cannot be loaded into the local database, it is only posible save it as OCI tar:
```
docker buildx build --no-cache --platform linux/amd64,linux/arm/v7 --tag "ssvembeddedde/pydslog2mqtt:0.1.0" --output type=oci,dest=pydslog2mqtt_0.1.0.tar .
```
