#!/bin/bash

vagrant up
# 1) Make sure we're in a virtual env
# 2) Add node to the path due to some ssh login but that changes the path
# 3) Build the files
# 4) run the dev server

vagrant ssh -c 'source /vagrant/vagrant-venv/bin/activate && export PATH="$PATH:$HOME/npm/bin:/home/vagrant/node_modules/.bin:$PATH" && export ENV="dev" && cd /vagrant/ && make build && make dev-requirements && make db-deploy && make dev-server'

# When dev server crashes or process is ended, shut down the VM
vagrant halt

