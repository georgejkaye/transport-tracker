FROM postgres:latest

COPY ./gen-data.sh /gen-data.sh
RUN chmod +x ./gen-data.sh

ENTRYPOINT [ "/gen-data.sh" ]
