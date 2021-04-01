#!/bin/bash

set -e
NAME="ssvembeddedde/pydslog2mqtt"
VERSION="$2"
DOCKERFILE="Dockerfile"

err() {
  echo "$1" >&2;
  exit 1;
}

build() {
  rm -rf build
  mkdir -p build
  cp -a app build/
  cp -a ../../PyDSlog build/app/
  cp -a Dockerfile build/
  cd build
}

# check input
[ -z "$VERSION" ] && err "Usage: build.sh dev|rel <version>"
[[ "$VERSION" =~ ^[0-9]+(\.[0-9]+){2}$ ]] || err "Error: Wrong version format, should be x.y.z"

case "$1" in
dev)
  docker image ls | grep "${NAME}" | grep -q "${VERSION}" && err "Error: Version ${VERSION} alredy exist"
  build
  docker build --no-cache --tag "${NAME}:${VERSION}" .
  ;;
rel)
  docker login https://index.docker.io/v1/
  build
  docker buildx build --no-cache --platform linux/amd64,linux/arm/v7 --tag "${NAME}:${VERSION}" --push .
  docker logout
  ;;
*)
  err "Usage: build.sh dev|rel <version>"
  ;;
esac
