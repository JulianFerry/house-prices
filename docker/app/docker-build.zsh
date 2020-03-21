#!/bin/zsh

script_dir=$(dirname $0:A);
project_path=$(dirname $(dirname $script_dir));
project_name=$(basename $project_path);
image_name=$project_name-app

export DOCKER_BUILDKIT=1

# Stop and remove project container if it exists. Remove image if it exists
echo "Removing container $image_name and image $image_name"
docker ps       | grep -q $image_name && docker stop $image_name;
docker ps -a    | grep -q $image_name && docker rm $image_name;
docker image ls | grep -q $image_name && docker rmi -f $image_name;

# Build project image and run new container
build_stage=${1:-release}
echo "Building image $image_name using multi-stage build up to stage: $build_stage"
if docker build \
  -t $image_name \
  -f $script_dir/Dockerfile \
  --target $build_stage \
  $project_path; then \
    if docker run -d --name $image_name -p 8080:8080 $image_name; then \
        echo "Container '$image_name' up and running at port 8080!"
        docker logs -f $image_name
    fi
fi
