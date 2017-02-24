#!/bin/sh
set -e

# We install a second time during a deploy due to google being a butthead 
# TODO - is this still necessary!?
pip install -r requirements.txt

npm install -g less
npm install -g eslint
