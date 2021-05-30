#!/bin/sh
# Small script to drop and delete OpenTSDB tables.
# This is a POWER user tool. Use with extreme care and precaution.

# Get 1st confirmation
while true; do
    read -p "Do you wish REALLY wish to delete all TSDB tables ? (y/n)" yn
    case $yn in
        [Yy]* ) echo "Hmmm...ok."; echo; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Get 2nd confirmation
while true; do
    read -p "Do you wish REALLY REALLY wish to delete all TSDB tables ? (y/n)" yn
    case $yn in
        [Yy]* ) echo "Ok...you asked for it!"; echo; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

test -n "$HBASE_HOME" || {
  echo >&2 'The environment variable HBASE_HOME must be set'
  exit 1
}
test -d "$HBASE_HOME" || {
  echo >&2 "No such directory: HBASE_HOME=$HBASE_HOME"
  exit 1
}

TSDB_TABLE=${TSDB_TABLE-'tsdb'}
UID_TABLE=${UID_TABLE-'tsdb-uid'}
TREE_TABLE=${TREE_TABLE-'tsdb-tree'}
META_TABLE=${META_TABLE-'tsdb-meta'}

# HBase scripts also use a variable named `HBASE_HOME', and having this
# variable in the environment with a value somewhat different from what
# they expect can confuse them in some cases.  So rename the variable.
hbh=$HBASE_HOME
unset HBASE_HOME
exec "$hbh/bin/hbase" shell <<EOF
disable '$UID_TABLE'
drop '$UID_TABLE'

disable '$TSDB_TABLE'
drop '$TSDB_TABLE'

disable '$TREE_TABLE'
drop '$TREE_TABLE'

disable '$META_TABLE'
drop '$META_TABLE'

EOF
