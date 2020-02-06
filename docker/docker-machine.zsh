#!/bin/zsh
# This script needs to be run with source $SCRIPT_NAME because of the 'eval' statement.

# set -x # echo on for debugging

docker-machine env default >/dev/null 2>&1 && \
echo "Connected to docker-machine 'default'." || \
    (docker-machine start default && \
    docker-machine env default 1>/dev/null && \
    echo "\nStarted docker-machine 'default'.");

eval $(docker-machine env default)

