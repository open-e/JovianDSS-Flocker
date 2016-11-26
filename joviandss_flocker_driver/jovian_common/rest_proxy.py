#    __             _                ___  __  __
#    \ \  _____   _(_) __ _ _ __    /   \/ _\/ _\
#     \ \/ _ \ \ / / |/ _` | '_ \  / /\ /\ \ \ \
#  /\_/ / (_) \ V /| | (_| | | | |/ /_// _\ \_\ \
#  \___/ \___/ \_/ |_|\__,_|_| |_/____/  \__/\__/
#
#
#    Copyright (c) 2016 Open-E, Inc.
#    All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json

import requests
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from base64 import b64encode
from . import exception as jexc



class JovianRESTProxy(object):
    """Jovian REST API proxy"""

    def __init__(self, LOG, config):
        """
        :param config: config is like dict
        """
        disable_warnings(InsecureRequestWarning)
        self.LOG = LOG
        self.user = config.get('jovian_user', 'admin')
        self.password = config.get('jovian_password', 'admin')
        self.retry_n = config.get('jovian_rest_send_repeats', 3)
        self.verify = False
        self.header = {'connection': 'keep-alive',
                       'Content-Type': 'application/json',
                       'authorization': 'Basic ' +
            b64encode('{}:{}'.format(self.user, self.password)).decode('utf-8')}

    def request(self, request_method, url, json_data=None):

        for i in range(self.retry_n):
            self.LOG.debug(
                "JovianDSS: Sending request of type {} to {}. \
                Attempt: {}.".format(request_method, url, i))
            try:

                ret = self.request_routine(url, request_method, json_data)

                # Work aroud for case when we have backend internal Fail.
                #                                           OS Fail
                if ret["code"] == 500:
                    if ret["error"] is not None:
                        if ("errno" in ret["error"]) and \
                                ("class" in ret["error"]):
                            if (ret["error"]["errno"] is 2) and\
                                    (ret["error"]["class"] ==
                                         "exceptions.OSError"):
                                self.LOG.error(
                                    "JovianDSS: Facing exceptions.OSError!")
                                continue

                return ret
            except requests.HTTPError as err:
                self.LOG.error("Unable to execute: {}".format(err))
                continue
            except requests.ConnectionError as err:
                self.LOG.error("Unable to execute: {}".format(err))

        raise jexc.JDSSRESTProxyException("Fail to execute {}, {} times in row."
                                          .format(url, self.retry_n))

    def request_routine(self, url, request_method, json_data=None):
        """Make an HTTPS request and return the results
        """

        response_obj = requests.request(request_method,
                                         url=url,
                                         headers=self.header,
                                         data=json.dumps(json_data),
                                         verify=self.verify)

        self.LOG.debug('JovianDSS: Response code: %s' %
                       response_obj.status_code)
        self.LOG.debug('JovianDSS: Response data: %s' % response_obj.text)

        ret = dict()
        ret['code'] = response_obj.status_code

        if '{' in response_obj.text and '}' in response_obj.text:
            if "error" in response_obj.text:
                ret["error"] = json.loads(response_obj.text)["error"]
            else:
                ret["error"] = None
            if "data" in response_obj.text:
                ret["data"] = json.loads(response_obj.text)["data"]
            else:
                ret["data"] = None

        return ret
