#!/usr/bin/env bash

PORT="${PORT:-8182}"
sed -i s/listen\ 80/listen\ $PORT/ /etc/nginx/conf.d/nginx.conf
