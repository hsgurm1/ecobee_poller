# ecobee_poller
This repository helps with visibility into working of Ecobee Smart themostat.

Stats are pulled from Ecobee API and indexed into InfluxDB, with Grafana Dashboard.

This repo is Dockerized version and update stats every 5 min.

Pre-requisites:
Docker / Docker-compose is in running state
Influxdb setup
Grafana setup


To begin with install and run process:
```
git clone https://github.com/hsgurm1/ecobee_poller.git
cd ecobee_poller/
docker build -t ecobee_poller:latest .
docker run -it -d ecobee_poller:latest
```

Stats will be pulled every 5 min. You can check current stats below;
```
docker logs --follow container-name
```

Example output:
```
2020-07-04 03:19:31,197 - ecobee - DEBUG - Initiated Ecobee poller at 2020-07-04 03:19:30.643818
2020-07-04 03:19:31,540 - ecobee - DEBUG - sensor readings written: 1
2020-07-04 03:19:31,540 - ecobee - DEBUG - -----------------------------------
Next run in 5 min
2020-07-04 03:19:31,540 - ecobee - DEBUG - -----------------------------------
2020-07-04 03:24:32,173 - ecobee - DEBUG - Initiated Ecobee poller at 2020-07-04 03:24:31.711358
2020-07-04 03:24:32,677 - ecobee - DEBUG - sensor readings written: 1
2020-07-04 03:24:32,698 - ecobee - DEBUG - -----------------------------------
```
