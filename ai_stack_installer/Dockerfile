FROM ubuntu:focal

ARG HBASE_BIN_DIR=/usr/share/hbase/hbase-1.4.14

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y sudo wget apt-utils dialog net-tools telnet tzdata \
    openjdk-8-jre-headless openjdk-8-jdk-headless gnuplot autoconf wireguard git

RUN export JAVA_HOME=/usr/lib/jvm/java-8-openjdk*

RUN apt-get clean && \
    rm -rf /var/lib/apt

RUN mkdir /srv/installer
COPY thirdparty/hbase* /srv/installer
COPY thirdparty/opentsdb* /srv/installer

COPY output/ai_stack_installer.tar.gz /srv/installer

RUN cd /srv/installer && \
    tar -xvf ai_stack_installer.tar.gz

RUN cd /srv/installer ; sudo ./pkg_install.sh ; sudo ./argusiot_service_stack_install_docker.sh

EXPOSE 4242

CMD /usr/share/hbase/hbase-1.4.14/bin/start-hbase.sh ; sleep 5; sudo service opentsdb start; while [ 1 ]; do sleep 1; done