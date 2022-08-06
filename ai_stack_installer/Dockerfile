FROM ubuntu:focal

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y sudo wget apt-utils dialog net-tools telnet tzdata \
    openjdk-8-jre-headless openjdk-8-jdk-headless gnuplot autoconf wireguard git

RUN export JAVA_HOME=/usr/lib/jvm/java-8-openjdk*

RUN apt-get clean && \
    rm -rf /var/lib/apt

RUN mkdir /srv/installer
COPY thirdparty/hbase* /srv/installer
COPY thirdparty/opentsdb* /srv/installer
COPY tsdb_in.txt /srv/installer

COPY output/ai_stack_installer.tar.gz /srv/installer

RUN cd /srv/installer && \
    tar -xvf ai_stack_installer.tar.gz

EXPOSE 4242

CMD cd /srv/installer ; sudo ./pkg_install.sh ; sudo ./argusiot_service_stack_install_docker.sh ; /bin/bash