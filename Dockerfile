FROM python:3.8.7-buster
RUN apt-get update
# && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends vim
#WORKDIR /tmp
#RUN curl -OL https://github.com/strukturag/libheif/releases/download/v1.10.0/libheif-1.10.0.tar.gz
#RUN tar xfz libheif-1.10.0.tar.gz
#WORKDIR /tmp/libheif-1.10.0
#RUN ./autogen.sh
#RUN ./configure
#RUN make
#RUN make install
WORKDIR /code/fix-image-mtime
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . /code/fix-image-mtime
CMD /bin/bash
