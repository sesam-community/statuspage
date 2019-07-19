#!/usr/bin/env python3

import datetime
import json
import logging
import os
import sys

import requests

__author__ = "Ravish Ranjan"

required_env_vars = ["SESAM_API_URL", "JWT", "PAGE_ID", "COMPONENT_ID", "API_KEY"]
optional_env_vars = ["GROUP_ID"]
status_page_base_url = 'https://api.statuspage.io/v1'


class AppConfig(object):
    pass


config = AppConfig()

# load variables
missing_env_vars = list()
for env_var in required_env_vars:
    value = os.getenv(env_var)
    if not value:
        missing_env_vars.append(env_var)
    setattr(config, env_var, value)

for env_var in optional_env_vars:
    value = os.getenv(env_var)
    if value:
        setattr(config, env_var, value)

# set logging
log_level = logging.getLevelName(os.environ.get('LOG_LEVEL', 'DEBUG'))  # default log level = INFO
logging.basicConfig(level=log_level)

logging.debug(datetime.datetime.now())
logging.debug(f"SESAM instance name: {config.SESAM_API_URL}")


def get_sesam_node_status():
    try:
        response = requests.get(url=config.SESAM_API_URL + "/health",
                                headers={'Authorization': 'bearer ' + config.JWT})
        if response.ok:
            return next(iter(response.json().values()))
        else:
            logging.error(f"Non 200 status code from the Sesam api, got: {response.status_code}")
    except requests.ConnectionError:
        logging.error(f"Issue while connecting  the SESAM Health api.")


def update_status_page(status_data):
    if hasattr(config, 'GROUP_ID'):
        payload = {'component': {'status': status_data, 'group_id': config.GROUP_ID}}
    else:
        payload = {'component': {'status': status_data}}
    json_data = json.dumps(payload)
    try:
        response = requests.patch(url=status_page_base_url + '/pages/' + config.PAGE_ID + '/components/' +
                                      config.COMPONENT_ID, data=json_data,
                                  headers={'Accept': 'application/json', 'Authorization': config.API_KEY})
        if response.ok:
            logging.info(f"OK, the status page has been updated successfully for component_id : {config.COMPONENT_ID}")
        else:
            logging.error(f"Some issue while updating the status page : {response.text}")
    except requests.ConnectionError:
        logging.error(f"Issue while connecting the status page api")


def prepare_payload(status_data):
    if status_data is not None:
        if status_data == 'ok':
            status_data = 'operational'
        else:
            status_data = 'major_outage'
        update_status_page(status_data)


if __name__ == '__main__':
    if len(missing_env_vars) != 0:
        logging.error(f"Missing the following required environment variable(s) {missing_env_vars}")
        sys.exit(1)
    else:
        prepare_payload(get_sesam_node_status())
