#!/bin/bash
set -e;
cd ~/project/dict_server
# docker build -f docker/Dockerfile -t dict_server .
docker build --platform linux/arm64 -f docker/Dockerfile -t dict_server:arm64 . --no-cache
docker build --platform linux/amd64 -f docker/Dockerfile -t dict_server .
# clear building cache
docker builder prune -f
# look docker occupy storage
docker system df

# tag repository
docker tag dict_server asia-east1-docker.pkg.dev/china-wall-over/dict-server/dict_server:v1.0
docker tag dict_server cia1099/dict_server:v1.0

# run container
docker run --name=dict_server --privileged -d --tmpfs /run --tmpfs /run/lock -p 22:22 -p 80:80 -p 443:443 -p 8866:8866 dict_server
docker run --name=dict_test -ti --rm --privileged -d --tmpfs /run --tmpfs /run/lock -p 8866:8866 dict_server

# extract assets from mdx
# mdict -x ~/Downloads/dict/oxfordstu.mdd -d dictionary/mdd