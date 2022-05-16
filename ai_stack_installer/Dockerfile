FROM ubuntu:focal

RUN apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo wget apt-utils dialog net-tools telnet tzdata

RUN  apt-get clean && \
    rm -rf /var/lib/apt

RUN mkdir /srv/installer

COPY output/ai_stack_installer.tar.gz /srv/installer

EXPOSE 4242

CMD ["/bin/bash"]