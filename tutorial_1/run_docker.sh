#!/bin/bash

# Variables for forwarding ssh agent into docker container
SSH_AUTH_ARGS=""
if [ ! -z $SSH_AUTH_SOCK ]; then
    DOCKER_SSH_AUTH_ARGS="-v $SSH_AUTH_SOCK:/run/host_ssh_auth_sock -e SSH_AUTH_SOCK=/run/host_ssh_auth_sock"
fi

# Settings required for having nvidia GPU acceleration inside the docker
DOCKER_GPU_ARGS="--env DISPLAY --env QT_X11_NO_MITSHM=1 --volume=/tmp/.X11-unix:/tmp/.X11-unix:rw"

dpkg -l | grep nvidia-container-toolkit &> /dev/null
HAS_NVIDIA_TOOLKIT=$?
which nvidia-docker > /dev/null
HAS_NVIDIA_DOCKER=$?
if [ $HAS_NVIDIA_TOOLKIT -eq 0 ]; then
  docker_version=`docker version --format '{{.Client.Version}}' | cut -d. -f1`
  if [ $docker_version -ge 19 ]; then
	  DOCKER_COMMAND="docker run --gpus all"
  else
	  DOCKER_COMMAND="docker run --runtime=nvidia"
  fi
elif [ $HAS_NVIDIA_DOCKER -eq 0 ]; then
  DOCKER_COMMAND="nvidia-docker run"
else
  echo "Running without nvidia-docker, if you have an NVidia card you may need it"\
  "to have GPU acceleration"
  DOCKER_COMMAND="docker run"
fi

DOCKER_NETWORK_ARGS="--net host"
if [[ "$@" == *"--net "* ]]; then
    DOCKER_NETWORK_ARGS=""
fi

xhost +

$DOCKER_COMMAND \
$DOCKER_GPU_ARGS \
$DOCKER_SSH_AUTH_ARGS \
$DOCKER_NETWORK_ARGS \
--privileged \
-v .:/home/user/devel \
-v /var/run/docker.sock:/var/run/docker.sock \
--rm --name hpp -it hpp:tuto
