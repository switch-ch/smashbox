from smashbox.script import config

import os.path
import datetime
import subprocess
import time

def get_oc_api():
    """ Returns an instance of the Client class

    :returns: Client instance
    """
    import owncloud

    protocol = 'http'
    if config.oc_ssl_enabled:
        protocol += 's'

    url = protocol + '://' + config.oc_server + '/' + config.oc_root
    #oc_api = owncloud.Client(url, verify_certs=False, debug=True)
    oc_api = owncloud.Client(url, verify_certs=False)
    return oc_api

oc_api = get_oc_api()
oc_api.login(config.oc_admin_user, config.oc_admin_password)

base_name = "test_load_tldrive"
for i in range(1,54):
    logger.info("Deleting user: %s%i"%(base_name,i))
    oc_api.delete_user("%s%i"%(base_name,i))
