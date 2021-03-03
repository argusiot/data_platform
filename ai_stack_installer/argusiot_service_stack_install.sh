#!/bin/bash
#
# Installer script for ArgusIoT Service Stack aka ai_service_stack
#

AI_HBASE_VERSION=1.4.13    # The Hbase version that works with OpenTSDB v2.4.0
AI_OPENTSDB_VERSION=2.4.0   # last stable OpenTSDB release
AI_GRAFANA_VERSION=7.3.2   # latest Grafana release

# Assume that all the supporting files needed for the install are present in
# current directory. User may override with a "-d <dir>".
ROOT_DIR=.
while getopts ":d:h" opt; do
  case $opt in
    d) ROOT_DIR="$OPTARG"
    ;;
    h) echo "$0 [-d <dir>]" ; echo ""; exit
  esac
done

#=====================
# Download and install Hbase

cd $HOME
mkdir ~/Downloads ; cd Downloads
wget https://downloads.apache.org/hbase/${AI_HBASE_VERSION}/hbase-${AI_HBASE_VERSION}-bin.tar.gz ; cd -
tar -xvf Downloads/hbase-${AI_HBASE_VERSION}-bin.tar.gz 
sudo apt-get --assume-yes update
sudo apt-get --assume-yes install openjdk-8-jre-headless
sudo apt-get --assume-yes install openjdk-8-jdk-headless # Optional - to get jps

# export JAVA_HOME=/usr
cp ${ROOT_DIR}/hbase-env.sh-reference hbase-${AI_HBASE_VERSION}/conf/hbase-env.sh

mkdir ~/hbase-operational-state
mv hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml-orig
cp ${ROOT_DIR}/hbase-site.xml-reference hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml

cd $HOME/hbase-${AI_HBASE_VERSION} ; bin/start-hbase.sh ; cd -

#Verify zookeeper has started:
# Expect to see: “Zookeeper version: 3.4.10 . . . . <more stuff>"
(echo "stat"; sleep 1; echo "quit") | telnet localhost 2181 > /tmp/zookeeper_foo
grep "Zookeeper version:" /tmp/zookeeper_foo
rm /tmp/zookeeper_foo


#=====================
# Download and install OpenTSDB

sudo apt-get --assume-yes install gnuplot
sudo apt-get --assume-yes install autoconf
sudo apt-get --assume-yes install python
cd Downloads 
wget https://github.com/OpenTSDB/opentsdb/releases/download/v${AI_OPENTSDB_VERSION}/opentsdb-${AI_OPENTSDB_VERSION}_all.deb
cd -
sudo dpkg -i Downloads/opentsdb-${AI_OPENTSDB_VERSION}_all.deb 

# Copy OpenTSDB config
mv /etc/opentsdb/opentsdb.conf /etc/opentsdb/opentsdb.conf-orig
cp ${ROOT_DIR}/opentsdb.conf-reference /etc/opentsdb/opentsdb.conf 

# Run script to create OpenTSDB tables

# ===== WARNINIG WARNING *** Create OpenTSDB Tables *** WARNING WARNING =====
# Current version of this script below ignores compression when creating tables.
# Sort this out later.
# ===========================================================================
cd $HOME/hbase-${AI_HBASE_VERSION}/
export HBASE_HOME=`pwd`
${ROOT_DIR}/create_opentsdb_hbase_tables.sh

echo "Waiting... to ensure that OpenTSDB tables creation succeeds !"
sleep 5

echo "Starting OpenTSDB..."
sudo service opentsdb start

sleep 5

# Verify OpenTSDB has started
(echo "version" ; sleep 1 ; echo "exit") | telnet localhost 4242 > /tmp/opentsdb_foo
echo ; grep ${AI_OPENTSDB_VERSION} /tmp/opentsdb_foo ; echo
rm /tmp/opentsdb_foo

# ====== End install OpenTSDB

#=====================
# Download and install Grafana
sudo apt-get install -y adduser libfontconfig1
cd $HOME/Downloads/
wget https://dl.grafana.com/oss/release/grafana_${AI_GRAFANA_VERSION}_amd64.deb
cd ..
sudo dpkg -i Downloads/grafana_${AI_GRAFANA_VERSION}_amd64.deb 

# Change the new user addition email tempate
sudo cp ${ROOT_DIR}/new_user_invite.html-reference $HOME/usr/share/grafana/public/emails

# To start grafana
sudo /bin/systemctl start grafana-server

# To start Grafana on reboot
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable grafana-server
#=====================


#=====================
# Download and install Wireguard

sudo apt-get --assume-yes install wireguard
sudo su
cd /etc/wireguard/
umask 077
wg genkey | tee privatekey | wg pubkey > publickey
cp ${ROOT_DIR}/wg0.conf-server-reference wg0.conf
echo "PrivateKey = `cat privatekey`" >> wg0.conf

sudo systemctl enable wg-quick@wg0   # to start Wireguard at boot time
sudo systemctl start wg-quick@wg0   # launch it now

# Show current status
sudo systemctl status wg-quick@wg0
sudo wg

#====================

echo "!!!!!! Installation almost complete !!!!"
echo ""
echo "To complete installation:"
echo "REMINDER: Override domain & root_url in grafana.ini with actual values"
echo "EXAMPLE: domain = ec2-44-241-74-152.us-west-2.compute.amazonaws.com"
echo "EXAMPLE: root_url = http://ec2-44-241-74-152.us-west-2.compute.amazonaws.com:3000/"
echo ""
echo "REMINDER: Restart grafana after overriding"
echo ""
echo ""
echo ""



