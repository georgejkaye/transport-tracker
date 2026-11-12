FROM postgres:latest

COPY migrate/migrate.sh .

COPY data data
COPY code code

ENTRYPOINT [ "/migrate.sh"]