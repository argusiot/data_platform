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

# Expected behaviour: Create the container images
init_docker_stack:
	docker network create --driver bridge argus_nw_bridge
	docker pull grafana/grafana-oss\:8.3.4-ubuntu
	docker build -f Dockerfile -t opentsdb .
	docker run -ditp 3000:3000 --name grafana --network argus_nw_bridge grafana/grafana-oss\:8.3.4-ubuntu
	docker run -itp 4242:4242 --name opentsdb --network argus_nw_bridge opentsdb

# Expected behavior: Clean up images
clean_docker_stack:
	docker stop opentsdb
	docker stop grafana
	docker container rm opentsdb
	docker container rm grafana
	docker rmi opentsdb
	docker rmi grafana/grafana-oss:8.3.4-ubuntu
	docker network rm argus_nw_bridge

# Start an existing container
start_docker_stack:
	docker start opentsdb
	docker start grafana

# Stop an existing container
stop_docker_stack:
	docker stop opentsdb
	docker stop grafana
