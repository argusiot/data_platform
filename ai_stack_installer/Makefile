FILE_LIST:= argusiot_service_stack_install.sh \
			hbase-env.sh-reference \
			create_opentsdb_hbase_tables.sh \
			hbase-site.xml-reference \
		  	opentsdb.conf-reference

installer_bundle:
	mkdir -p output
	tar -cvf output/ai_stack_installer.tar ${FILE_LIST}
	gzip output/ai_stack_installer.tar

clean:
	rm -rf output
