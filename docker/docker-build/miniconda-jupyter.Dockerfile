FROM continuumio/miniconda3:latest 
#intelpython/intelpython3_core:latest

LABEL MAINTAINER="Julian Ferry <julianferry94@gmail.com>"

VOLUME /project
WORKDIR /project

ADD requirements.txt /

# Save errors to a log file, rather than crash the RUN command halfway through (https://stackoverflow.com/questions/30716937/dockerfile-build-possible-to-ignore-error)
RUN while read requirement; do conda install --yes $requirement; done < requirements.txt 2>conda_install.log || echo "\nSome `conda install` operations failed! Check conda_install.log for the specific error messages.\n"

EXPOSE 8888

CMD jupyter notebook --ip='0.0.0.0' --port=8888 --allow-root --no-browser
