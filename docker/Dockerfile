FROM ubuntu:latest
MAINTAINER harman@soconsulting.ca

ENV APIValue="enter-your-api-value-here"
ENV influxdb_server_value='influx_db_server_ip'
ENV influxdb_port_value=8086
ENV influxdb_database_value='ecobee'
ENV filepath="/var/log/ecobee.log"


RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-pip \
        python3-distutils \
        python3-setuptools \
        vim


RUN pip3 install influxdb

COPY poller.py /etc/poller.py

COPY run.sh /etc/run.sh
RUN chmod +x /etc/run.sh


COPY .ecobee_token /root/

ENTRYPOINT ["/etc/run.sh"]
