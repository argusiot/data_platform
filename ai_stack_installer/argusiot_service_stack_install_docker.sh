#!/bin/bash
#
# Installer script for ArgusIoT Service Stack aka ai_service_stack
#

AI_HBASE_VERSION=1.4.14    # The Hbase version that works with OpenTSDB v2.4.0
AI_OPENTSDB_VERSION=2.4.0   # last stable OpenTSDB release
AI_GRAFANA_VERSION=8.3.4   # latest Grafana release

HBASE_DIR='/usr/share/hbase'

# Assume that all the supporting files needed for the install are present in
# current directory. User may override with a "-d <dir>".
BASE_DIR=`pwd`
while getopts ":d:h" opt; do
  case $opt in
    d) BASE_DIR="$OPTARG"
    ;;
    h) echo "$0 [-d <dir>]" ; echo ""; exit
  esac
done

#=====================
# Download and install Hbase

cd ${BASE_DIR}

wget https://archive.apache.org/dist/hbase/${AI_HBASE_VERSION}/hbase-${AI_HBASE_VERSION}-bin.tar.gz ;

echo "Creating ${HBASE_DIR} for HBase install"
mkdir -p ${HBASE_DIR}
cd ${HBASE_DIR}
tar -xvf ${BASE_DIR}/hbase-${AI_HBASE_VERSION}-bin.tar.gz
sudo apt-get --assume-yes update
sudo apt-get --assume-yes install openjdk-8-jre-headless
sudo apt-get --assume-yes install openjdk-8-jdk-headless # Optional - to get jps

# export JAVA_HOME=/usr
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

cp ${BASE_DIR}/hbase-env.sh-reference ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-env.sh

mv ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml-orig
cp ${BASE_DIR}/hbase-site.xml-reference ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml

cd ${HBASE_DIR}/hbase-${AI_HBASE_VERSION} ; bin/start-hbase.sh
cd ${BASE_DIR}

#Verify zookeeper has started:
# Expect to see: “Zookeeper version: 3.4.10 . . . . <more stuff>"
(echo "stat"; sleep 1; echo "quit") | telnet localhost 2181 > /tmp/zookeeper_foo
grep "Zookeeper version:" /tmp/zookeeper_foo
rm /tmp/zookeeper_foo


#=====================
# Download and install OpenTSDB

cd ${BASE_DIR}
sudo apt-get --assume-yes install gnuplot
sudo apt-get --assume-yes install autoconf
sudo apt-get --assume-yes install python

wget https://github.com/OpenTSDB/opentsdb/releases/download/v${AI_OPENTSDB_VERSION}/opentsdb-${AI_OPENTSDB_VERSION}_all.deb

sudo dpkg -i ${BASE_DIR}/opentsdb-${AI_OPENTSDB_VERSION}_all.deb

# Copy OpenTSDB config
mv /etc/opentsdb/opentsdb.conf /etc/opentsdb/opentsdb.conf-orig
cp ${BASE_DIR}/opentsdb.conf-reference /etc/opentsdb/opentsdb.conf

# Run script to create OpenTSDB tables

# ===== WARNINIG WARNING *** Create OpenTSDB Tables *** WARNING WARNING =====
# Current version of this script below ignores compression when creating tables.
# Sort this out later.
# ===========================================================================
cd ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/
export HBASE_HOME=`pwd`
${BASE_DIR}/create_opentsdb_hbase_tables.sh
${BASE_DIR}/enable_tsdb_table_compression.sh

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
# sudo apt-get install -y adduser libfontconfig1
# cd ${BASE_DIR}
# wget https://dl.grafana.com/oss/release/grafana_${AI_GRAFANA_VERSION}_amd64.deb
# sudo dpkg -i ${BASE_DIR}/grafana_${AI_GRAFANA_VERSION}_amd64.deb

# # Update grafana.ini
# sudo cp ${BASE_DIR}/grafana.ini-reference /etc/grafana/grafana.ini

# # Change the new user addition email tempate
# sudo cp ${BASE_DIR}/new_user_invite.html-reference /usr/share/grafana/public/emails/new_user_invite.html

# # To start grafana
# sudo /bin/systemctl start grafana-server

# # Install Grafana plug-ins we rely upon
# sudo grafana-cli plugins install grafana-piechart-panel
# sudo grafana-cli plugins install agenty-flowcharting-panel
# sudo /bin/systemctl restart grafana-server


# # To start Grafana on reboot
# sudo /bin/systemctl daemon-reload
# sudo /bin/systemctl enable grafana-server
#=====================


#=====================
# Download and install Wireguard

sudo apt-get --assume-yes install wireguard
cd /etc/wireguard/
umask 077

# Generate public and private keys for the VPN interface
wg genkey | tee privatekey | wg pubkey > publickey

# Generate the vpn_data interface config file from the config template (aka
# the reference file) by replacing the private key from the template with
# actual value.
placeholder_value="PrivateKey = PLACEHOLDER_REPLACE_WITH_GENERATED_KEY"
actual_value="PrivateKey = `cat privatekey`"
sed "s/$placeholder_value/$actual_value/g" ${BASE_DIR}/vpn_data.conf-server-reference > vpn_data.conf

sudo systemctl enable wg-quick@vpn_data   # to start Wireguard at boot time
sudo systemctl start wg-quick@vpn_data   # launch it now

# Show current status
sudo systemctl status wg-quick@vpn_data | cat
sudo wg

#====================

echo "!!!!!! Installation almost complete !!!!"
echo ""
echo "To complete installation:"
echo "REMINDER: 1) Override domain grafana.ini with actual value"
echo "EXAMPLE: domain = ec2-44-241-74-152.us-west-2.compute.amazonaws.com"
echo ""
echo "REMINDER: 2) Does SMTP config need to be changed ?"
echo "REMINDER:    SMTP is currently configured to use demoguy@argus... !"
echo ""
echo "REMINDER: 3) admin, please change org name after 1st login !"
echo ""
echo "REMINDER: Restart grafana after overriding"
echo ""
echo ""
echo ""
