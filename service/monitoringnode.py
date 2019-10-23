#!/usr/bin/env python3

import datetime
import json
import logging
import os
import sys
from emailsender import Emailsender

import requests

__author__ = "Ravish Ranjan"

required_env_vars = ["SESAM_API_URL", "JWT", "PAGE_ID", "COMPONENT_ID", "API_KEY"]
optional_env_vars = ["GROUP_ID"]
email_env_vars = ["RECIPIENTS", "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_SENDER"]
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

EmailFunctionality = False
missing_email_env_vars = []
for env_var in email_env_vars:
    value = os.getenv(env_var)
    if value:
        if env_var == 'RECIPIENTS':
            setattr(config, 'RECIPIENTS', json.loads(value))#Get it as list from string.
        else:
            setattr(config, env_var, value)
            EmailFunctionality = True
    elif not value and EmailFunctionality:
        missing_email_env_vars.append(env_var)

# set logging
log_level = logging.getLevelName(os.environ.get('LOG_LEVEL', 'DEBUG'))  # default log level = INFO
logging.basicConfig(level=log_level)

logging.debug(datetime.datetime.now())
logging.debug(f"SESAM instance name: {config.SESAM_API_URL}")


def get_sesam_node_status():
    try:
        response = requests.get(url=config.SESAM_API_URL + "/api/health",
                                headers={'Authorization': 'bearer ' + config.JWT})
        if response.status_code == 200:
            return 'OK'
        else:
            logging.error(f"Non 200 status code from the Sesam api, got: {response.status_code}")
            return 'NOT OK'
    except requests.ConnectionError as e:
        logging.error(f"Issue while connecting  the SESAM Health api {e}.")
        return 'NOT OK'

def get_node_type():
    try:
        response = requests.get(url=config.SESAM_API_URL + '/api/datasets/system:config:aggregator',
                                headers={'Authorization': 'bearer ' + config.JWT})

        if response.status_code == 200:
            return 'MULTI'
        else:
            return 'SINGLE'

    except Exception('Problem connecting to sesam node') as e:
        raise e


def get_subnodes_status(subnodes):
    try:
        with requests.session() as session:
            problematic_subnodes = []
            for s in subnodes:
                try:
                    response = session.get(url="{}/_/{}/api/health".format(config.SESAM_API_URL, s), timeout=180,
                                       headers={'Authorization': 'bearer ' + config.JWT})
                    if response.status_code != 200:
                        problematic_subnodes.append(s)
                except Exception as e:
                    problematic_subnodes.append(s)

            return problematic_subnodes
    except Exception as e:
        logging.error(f"issue when creating connection to check subnodes status{e}")
        raise e


def get_subnodes_from_dataset():
    try:
        response = requests.get(url=config.SESAM_API_URL + '/api/datasets/system:config:aggregator/entities/apiconfig',
                                headers={'Authorization': 'bearer ' + config.JWT})
        subnodes = [e for e in json.loads(response.content)['endpoints']]
        return subnodes

    except Exception('Problem getting subnodes from system:config:aggregator dataset') as e:
        raise e


def get_sesam_subnodes_status():
    try:
        dataset_subnodes = get_subnodes_from_dataset()
        if not dataset_subnodes:#Safeguard: If functions returned None
            return 'NOT OK'
        faulty_subnodes = get_subnodes_status(dataset_subnodes)#Get status of problematic subnodes

        if len(faulty_subnodes) != 0:
            logging.error(f"Problem with subnodes: {faulty_subnodes}")#Future maybe post this to dataset for emailing.
            return faulty_subnodes
        else:
            return 'OK'

    except Exception as e:
        logging.error(f"Catched error: {e}")
        return 'NOT OK'


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
        if status_data == 'OK':
            status_data = 'operational'
        else:
            try:
                if EmailFunctionality:
                    sender = Emailsender(config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.SMTP_SENDER)
                    logging.info(sender.sendMail(config.RECIPIENTS, 'Problems with node {}'.format(config.SESAM_API_URL), status_data))
            except Exception as e:
                logging.error('Failed to send email because of {}'.format(e))
            status_data = 'major_outage'
        update_status_page(status_data)


if __name__ == '__main__':
    if len(missing_env_vars) != 0:
        logging.error(f"Missing the following required environment variable(s) {missing_env_vars}")
        sys.exit(1)
    elif config.SESAM_API_URL.endswith('/api'):#Backwards compatability
        setattr(config, 'SESAM_API_URL', config.SESAM_API_URL[0:-4])

    if EmailFunctionality and len(missing_email_env_vars) != 0:
        logging.error("Some email variables set but not all! Missing: ".format(missing_email_env_vars))

    try:
        if get_node_type() == 'MULTI':
            prepare_payload(get_sesam_subnodes_status())
        else:
            prepare_payload(get_sesam_node_status())
    except Exception as e:
        logging.error(f"Issue getting node type, {e}")
        prepare_payload('Issue getting node type')
    sys.exit(0)
