FILE_LIST:= argusiot_service_stack_install.sh \
			argusiot_service_stack_install_docker.sh \
			pkg_install.sh \
			hbase-env.sh-reference \
			create_opentsdb_hbase_tables.sh \
			drop_opentsdb_tables.sh \
			enable_tsdb_table_compression.sh \
			hbase-site.xml-reference \
			http_post_using_json_simple_script.py \
			opentsdb.conf-reference \
			grafana.ini-reference \
			new_user_invite.html-reference \
			vpn_data.conf-server-reference \

installer_bundle:
	mkdir -p output
	tar -cvf output/ai_stack_installer.tar ${FILE_LIST}
	gzip output/ai_stack_installer.tar

clean:
	rm -rf output

init_stack:
	docker network create --driver bridge argus
	docker pull grafana/grafana-oss\:8.3.4-ubuntu
	docker build -f Dockerfile -t opentsdb .
	docker run -ditp 3000:3000 --name grafana --network argus grafana/grafana-oss\:8.3.4-ubuntu
	docker run -itp 4242:4242 --name opentsdb --network argus --mount 'type=volume,src=opentsdb_hour,dst=/data/argusiot/hbase,volume-driver=local' opentsdb

close_stack:
	docker stop opentsdb -t 30
	docker stop grafana
	docker container rm opentsdb
	docker container rm grafana
	docker rmi opentsdb
	docker rmi grafana/grafana-oss:8.3.4-ubuntu
	docker network rm argus