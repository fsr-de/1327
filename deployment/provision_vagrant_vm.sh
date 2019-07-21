set -x # print executed commands

export DEBIAN_FRONTEND=noninteractive

# install python stuff
apt-get -q update
apt-get -q install -y python3-dev python3-pip gettext

# setup Yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list

apt-get update
apt-get -q install -y yarn

yarn global add less

# setup postgres
apt-get -q install -y postgresql
sudo -u postgres createuser --createdb 1327
sudo -u postgres psql -U postgres -d postgres -c "ALTER USER \"1327\" WITH PASSWORD '1327';"
sudo -u postgres createdb -O 1327 1327

# alias python -> python3
echo "alias python=python3" >> /home/vagrant/.bashrc

# auto cd into /vagrant on login
echo "cd /vagrant" >> /home/vagrant/.bashrc

# install requirements
sudo -H -u vagrant pip3 install --user -r /vagrant/requirements-test.txt
sudo -H -u vagrant pip3 install --user psycopg2==2.7.3.1

# deploy localsettings and insert random key
cp /vagrant/deployment/localsettings.template.py /vagrant/_1327/localsettings.py
sed -i -e "s/\${SECRET_KEY}/`sudo head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32`/" /vagrant/_1327/localsettings.py

# setup static files
cd /vagrant/_1327/static
sudo -H -u vagrant yarn --no-bin-links

# setup 1327
cd /vagrant
sudo -H -u vagrant python3 manage.py migrate --noinput
sudo -H -u vagrant python3 manage.py collectstatic --noinput
sudo -H -u vagrant python3 manage.py compilemessages
