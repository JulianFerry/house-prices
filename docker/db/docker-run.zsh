#!/bin/zsh

script_dir=$(dirname $0:A);
project_dir=$(dirname $(dirname $script_dir));

docker run \
    -d \
    --name mysql \
    -e MYSQL_ROOT_PASSWORD=root \
    -v $project_dir/db:/var/lib/mysql \
    -p 3306:3306 \
    mysql
