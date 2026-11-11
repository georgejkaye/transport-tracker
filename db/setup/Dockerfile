FROM postgres:latest

COPY extensions.sql .
COPY dump_db_to_file.sh .
COPY restore_db_from_dump.sh .
COPY populate_db_docker_volume.sh .

RUN chmod +x populate_db_docker_volume.sh

ENTRYPOINT [ "/populate_db_docker_volume.sh" ]
