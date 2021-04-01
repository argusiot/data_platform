#!/bin/sh
# Small script to enable GZ compression for the 'tsdb' table.

test -n "$HBASE_HOME" || {
  echo >&2 'The environment variable HBASE_HOME must be set'
  exit 1
}
test -d "$HBASE_HOME" || {
  echo >&2 "No such directory: HBASE_HOME=$HBASE_HOME"
  exit 1
}

TSDB_TABLE=${TSDB_TABLE-'tsdb'}

# HBase scripts also use a variable named `HBASE_HOME', and having this
# variable in the environment with a value somewhat different from what
# they expect can confuse them in some cases.  So rename the variable.
hbh=$HBASE_HOME
unset HBASE_HOME
exec "$hbh/bin/hbase" shell <<EOF
disable '$TSDB_TABLE'
alter '$TSDB_TABLE',{NAME=>'t',COMPRESSION=>'GZ'}
enable '$TSDB_TABLE'
desc '$TSDB_TABLE'
EOF
