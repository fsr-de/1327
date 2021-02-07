#!/bin/bash

# installed with https://computingforgeeks.com/how-to-install-latest-rabbitmq-server-on-ubuntu-linux/
apt-get -q install -y rabbitmq-server

#mkdir /opt/redis

#cd /opt/redis
# Use latest stable
#wget -q http://download.redis.io/redis-stable.tar.gz
# Only update newer files
#tar -xz --keep-newer-files -f redis-stable.tar.gz

#cd redis-stable
#make
#make install
#mkdir -p /etc/redis
#mkdir /var/lib/redis
#chmod -R 770 /var/lib/redis
#adduser --system --group --no-create-home redis
#chown redis:redis /var/lib/redis

# rabbitmq port 55672
#cp -u /vagrant/deployment/redis/redis.conf /etc/redis/6379.conf
#cp -u /vagrant/deployment/redis/redis.service /etc/systemd/system/redis.service

systemctl enable rabbitmq-server
systemctl start rabbitmq-server
