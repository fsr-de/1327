#!/bin/bash

# installed with https://computingforgeeks.com/how-to-install-latest-rabbitmq-server-on-ubuntu-linux/
sudo apt-get -q install -y rabbitmq-server

systemctl enable rabbitmq-server
systemctl start rabbitmq-server
