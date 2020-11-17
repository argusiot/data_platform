#
# Installer script for ArgusIoT Service Stack aka ai_service_stack
#

AI_HBASE_VERSION=1.4.13    # The Hbase version that works with OpenTSDB v2.4.0
AI_OPENTSDB_VERSION=2.4.0   # last stable OpenTSDB release
AI_GRAFANA_VERSION=7.3.2   # latest Grafana release


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
cp /vagrant/hbase-env.sh-reference hbase-${AI_HBASE_VERSION}/conf/hbase-env.sh

mkdir ~/hbase-operational-state
mv hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml-orig
cp /vagrant/hbase-site.xml-reference hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml

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
cp /vagrant/opentsdb.conf-reference /etc/opentsdb/opentsdb.conf 

# Run script to create OpenTSDB tables

# ===== WARNINIG WARNING *** Create OpenTSDB Tables *** WARNING WARNING =====
# Current version of this script below ignores compression when creating tables.
# Sort this out later.
# ===========================================================================
cd $HOME/hbase-${AI_HBASE_VERSION}/
export HBASE_HOME=`pwd`
/vagrant/create_opentsdb_hbase_tables.sh

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

# To start grafana
sudo /bin/systemctl start grafana-server

# To start Grafana on reboot
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable grafana-server
#=====================


echo "!!!!!! Installation complete !!!!"


