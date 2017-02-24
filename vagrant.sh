#!/bin/bash
set -e

# This file is used by the Vagrantfile to set up the dev environment

sudo apt-get update

sudo apt-get install --yes --force-yes zip unzip python python-dev \
    build-essential curl redis-server python-setuptools
easy_install -U pip

debconf-set-selections <<< 'mysql-server mysql-server/root_password password bacon'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password bacon'
apt-get update --yes --force-yes
apt-get install --yes --force-yes python-software-properties python-mysqldb mysql-server libmysqlclient-dev \
    libffi-dev libssl-dev

printf "[client]\nuser = root\npassword = bacon" >> ~/.my.cnf

service mysql restart
mysql -e "create database dev;"


curl -sL https://deb.nodesource.com/setup | bash -
sudo apt-get --yes --force-yes install nodejs

# let's get some docker going too
curl -sSL https://get.docker.com/ | sh

# have to do some weird shit to get nodejs to work without sudo -.-
su vagrant -l -c 'npm config set prefix ~/npm'
echo 'export PATH="$PATH:$HOME/npm/bin:/home/vagrant/node_modules/.bin:$PATH"' >> /home/vagrant/.bashrc
echo 'export ENV="dev"' >> /etc/profile
echo 'export PYTHONPATH="/vagrant/"' >> /etc/profile

# Get some virtualenv shit going all up in here
pip install virtualenv
echo "source /vagrant/vagrant-venv/bin/activate" >> $HOME/.bashrc
echo "source /vagrant/vagrant-venv/bin/activate" >> /home/vagrant/.bashrc

# Install cron job
echo '* * * * * root curl --user staffjoydev: http://suite.local/api/v2/internal/cron/' >> /etc/crontab

cd /vagrant/ && rm -rf vagrant-venv && virtualenv vagrant-venv
source /vagrant/vagrant-venv/bin/activate && export PATH="$PATH:$HOME/npm/bin:/home/vagrant/node_modules/.bin:$PATH" && export ENV="dev" && cd /vagrant/ && make build && make dev-requirements && make db-deploy
python /vagrant/dev-sudo.py

