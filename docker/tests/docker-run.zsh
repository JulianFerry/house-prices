#!/bin/zsh

script_path=$0:A;
project_path=$(dirname $(dirname $(dirname $script_path)));
project_name=$(basename $project_path);

gitlab_ci_pre_clone_script="'
    umount /$project_name; \
    mv $project_name "$project_name"_copy; \
    cp -r "$project_name"_tmp $project_name; \
    cd $project_name; \
    git clean -xdf; \
    git init; \
    git config --global user.email \"julianferry94@gmail.com\";' "

if docker run --rm -d \
  --name $project_name-gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $project_path:/$project_name \
  gitlab/gitlab-runner; then \
    docker exec $project_name-gitlab-runner /bin/bash -c " \
    cd $project_name; \
    gitlab-runner exec docker \
      --pre-clone-script $gitlab_ci_pre_clone_script \
      --docker-privileged \
      --docker-pull-policy 'if-not-present' \
      --docker-volumes $project_path:/"$project_name"_tmp \
      test;";

  docker stop $project_name-gitlab-runner
fi
