#!/bin/bash
set -e;
cd ~/project/dict_server
# docker build -f docker/Dockerfile -t dict_server .
docker build --platform linux/arm64 -f docker/Dockerfile -t dict_server:arm64 .
docker build --platform linux/amd64 -f docker/Dockerfile -t dict_server .

# run container
docker run --name=dict_server --privileged -d --tmpfs /run --tmpfs /run/lock -p 22:22 -p 80:80 -p 443:443 -p 8866:8866 dict_server
docker run --name=dict_test -ti --rm --privileged -d --tmpfs /run --tmpfs /run/lock -p 8866:8866 dict_server