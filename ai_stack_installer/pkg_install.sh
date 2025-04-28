#!/bin/bash
#
# Installer script for ArgusIoT Service Stack dependencies aka openTSDB & HBase
#

AI_HBASE_VERSION=1.4.14    # The Hbase version that works with OpenTSDB v2.4.0
AI_OPENTSDB_VERSION=2.4.1   # last stable OpenTSDB release
AI_GRAFANA_VERSION=8.3.4   # latest Grafana release

HBASE_DIR='/usr/share/hbase'

BASE_DIR=`pwd`

cd ${BASE_DIR}

#===========================
# Run HBase

mkdir -p ${HBASE_DIR}
cd ${HBASE_DIR}
tar -xvf ${BASE_DIR}/hbase-${AI_HBASE_VERSION}-bin.tar.gz

cp ${BASE_DIR}/hbase-env.sh-reference ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-env.sh
mv ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml-orig
cp ${BASE_DIR}/hbase-site.xml-reference ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/conf/hbase-site.xml

cd ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}
bin/start-hbase.sh
cd ${BASE_DIR}

#==============================
# Run openTSDB

sudo dpkg -i ${BASE_DIR}/opentsdb-${AI_OPENTSDB_VERSION}_all.deb

mv /etc/opentsdb/opentsdb.conf /etc/opentsdb/opentsdb.conf-orig
cp ${BASE_DIR}/opentsdb.conf-reference /etc/opentsdb/opentsdb.conf

cd ${HBASE_DIR}/hbase-${AI_HBASE_VERSION}/
export HBASE_HOME=`pwd`
${BASE_DIR}/create_opentsdb_hbase_tables.sh
${BASE_DIR}/enable_tsdb_table_compression.sh

sleep 5