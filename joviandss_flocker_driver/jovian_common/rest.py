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

from . import rest_proxy
from . import jdss_common as jcom
from . import exception as jexc


class JovianRESTAPI(object):
    """Jovian REST API proxy"""

    def __init__(self, LOG, config):
        """
        :param config: config is like dict
        """

        self.LOG = LOG
        self.url = config.get('jovian_rest_protocol', 'https') + '://' + \
                   config.get('jovian_host') + ':' + \
                   str(config.get('jovian_rest_port'))

        self.LOG.debug("JovianDSS: rest api base url: {}".format(self.url))
        self.api_path = "/api/v2"
        self.timeout = 60

        self.rproxy = rest_proxy.JovianRESTProxy(self.LOG, config)

    def is_pool_exists(self, pool_name):
        """is_pool_exists
        GET
        /pools/<string:poolname>

        :param pool_name:
        :return: Bool
        """
        path = self.api_path + '/pools/' + pool_name
        req = self.url + path
        self.LOG.debug("JovianDSS: check pool: {}".format(req))

        resp = self.rproxy.request('GET', req)

        if resp["code"] != 200 or resp["error"] is not None:
            return False

        return True

    def get_luns(self, pool_name):

        """get_all_pool_volumes
        GET
        /pools/<string:poolname>/volumes
        :param pool_name
        :return list of all pool volumes
        """
        path = self.api_path + '/pools/' + pool_name + '/volumes'

        req = self.url + path

        self.LOG.debug("JovianDSS: get all pool volumes [url]: {}".format(req))
        resp = self.rproxy.request('GET', req)

        if resp['error'] is None and resp['code'] == 200:
            return resp['data']
        else:
            raise jexc.JDSSRESTException(resp['error']['message'])

    def create_lun(self, pool_name, volume_name, volume_size):
        """create_volume
        POST
        /pools/<string:poolname>/volumes

        :param pool_name:
        :param volume_name:
        :param volume_size:
        :return:
        """
        path = self.api_path + '/pools/' + pool_name + '/volumes'
        volume_size_str = str(volume_size)
        jbody = {
            'name': volume_name,
            'size': volume_size_str
        }

        req = self.url + path

        self.LOG.debug("JovianDSS: create lun [url]: {}".format(req))
        resp = self.rproxy.request('POST', req, json_data=jbody)

        if resp["error"] is None and resp["code"] == 200:
            return

        if resp["error"] is not None:
            if resp["error"]["errno"] == str(5):
                raise jexc.JDSSRESTException(
                    'Failed to create volume. {}.'.format(
                                                    resp['error']['message']))

        raise jexc.JDSSRESTException('Failed to create volume.')

    def extend_lun(self, pool_name, volume_name, volume_size):
        """create_volume
        POST
        /pools/<string:poolname>/volumes
        """

        path = self.api_path + '/pools/' + pool_name + '/volumes/' + volume_name
        #TODO:rethink volume size
        volume_size_str = str(volume_size)
        jbody = {
            'size': volume_size_str
        }

        req = self.url + path

        self.LOG.debug("JovianDSS: extend lun [url]: {}".format(req))
        resp = self.rproxy.request('PUT', req, json_data=jbody)

        if resp["error"] is None and resp["code"] == 201:
            return

        if resp["error"] is not None:
            raise jexc.JDSSRESTException(
                'Failed to extend volume. {}.'.format(resp['error']['message']))

        raise jexc.JDSSRESTException('Failed to create volume.')

    def is_lun(self, pool_name, volume_name):
        """
        Returns True if volume exists. Uses GET request.
        :param pool_name:
        :param volume_name:
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + '/volumes/' + volume_name
        req = self.url + path

        self.LOG.debug("JovianDSS: check lun [url]: {}".format(req))
        ret = self.rproxy.request('GET', req)

        if ret["error"] is None and ret["code"] == 200:
            return True
        return False

    def get_lun(self, pool_name, volume_name):
        """get_lun
        GET
        /pools/<pool_name>/volumes/<volume_name>

        :param pool_name:
        :param volume_name:
        :return:
        {
            "data":
            {
                "origin": null,
                "referenced": "65536",
                "primarycache": "all",
                "logbias": "latency",
                "creation": "1432730973",
                "sync": "always",
                "is_clone": false,
                "dedup": "off",
                "used": "1076101120",
                "full_name": "Pool-0/v1",
                "type": "volume",
                "written": "65536",
                "usedbyrefreservation": "1076035584",
                "compression": "lz4",
                "usedbysnapshots": "0",
                "copies": "1",
                "compressratio": "1.00x",
                "readonly": "off",
                "mlslabel": "none",
                "secondarycache": "all",
                "available": "976432152576",
                "resource_name": "Pool-0/v1",
                "volblocksize": "131072",
                "refcompressratio": "1.00x",
                "snapdev": "hidden",
                "volsize": "1073741824",
                "reservation": "0",
                "usedbychildren": "0",
                "usedbydataset": "65536",
                "name": "v1",
                "checksum": "on",
                "refreservation": "1076101120"
            },
            "error": null
        }
        """
        path = self.api_path + '/pools/' + pool_name + '/volumes/' + volume_name

        req = self.url + path

        self.LOG.debug("JovianDSS: get all pool volumes [url]: {}".format(req))
        resp = self.rproxy.request('GET', req)

        if resp['error'] is None and resp['code'] == 200:
            return resp['data']
        else:
            raise jexc.JDSSRESTException(resp['error']['message'])

    def delete_lun(self, pool_name, volume_name):
        """delete_volume
        DELETE
        /pools/<string:poolname>/volumes/<string:volumename>

        :param pool_name:
        :param volume_name:
        :return:
        """

        if not self.is_lun(pool_name, volume_name):
            return

        path = self.api_path + '/pools/' + pool_name + '/volumes/' + volume_name

        req = self.url + path
        self.LOG.debug("JovianDSS: delete lun [url]: {}".format(req))

        resp = self.rproxy.request('DELETE', req)

        if ((resp["code"] == 200) or
                (resp["code"] == 201) or
                (resp["code"] == 204)):
            self.LOG.debug(
                "JovianDSS: LUN DELETE SUCCESS exiting. {}".format(req))
            return

        # TODO: implement handling of situations when volume can't be deleted or
        #  it was already deleted

        # raise jexc.JDSSRESTException(_("volume is busy"))
        # raise jexc.JDSSRESTException(_("volume is dne"))

        if resp["error"] is not None:
            if "errno" in resp["error"]:
                if resp["error"]["errno"] == 1:
                    return

        raise jexc.JDSSRESTException('Failed to delete volume.')

    def get_targets(self, pool_name):

        """list_targets
        GET
        /pools/<string:poolname>/san/iscsi/targets
        :param pool_name
        :return list of all pool targets
        """
        if self.is_pool_exists(pool_name):

            path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets'

            req = self.url + path

            self.LOG.debug("JovianDSS: get list targets [url]: {}".format(req))
            resp = self.rproxy.request('GET', req)

            if resp['error'] is None and resp['code'] == 200:
                return resp['data']
            else:
                raise jexc.JDSSRESTException(resp['error']['message'])

        else:
            raise jexc.JDSSRESTException("Pool isn't exist")


    def get_zvol_info(self, pool_name, lun_name):
        """get_zvol_info
        GET
        /pools/ pool_name /san/iscsi/targets/ target_name /luns/ lun_name
        :param pool_name:
        :param lun_name:
        :return:
        {
            "data": {
                "name": "4",
                "blocksize": "512",
                "mode": "ro",
                "scsiid": "6778da4b1cb60221",
                "type": "volume",
                "lun": "1"
            },
            "error": null
        }
        """

        target_name = jcom.get_jprefix() + lun_name

        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets/' + \
            target_name + "/luns/" + lun_name
        req = self.url + path

        self.LOG.debug("JovianDSS: check lun [url]: {}".format(req))
        resp = self.rproxy.request('GET', req)

        if resp["error"] is None and resp["code"] == 200:
            return resp["data"]

        # TODO: provide additional handling of different error cases
        raise jexc.JDSSRESTException(
            'Failed to get zvol {}.'.format(resp['error']['message']))

    def is_target(self, pool_name, target_name):
        """is_target
        GET
        /pools/ pool_name /san/iscsi/targets/ target_name
        :param pool_name:
        :param target_name:
        :return: Bool
        """
        path = self.api_path + \
            '/pools/' + pool_name + \
            '/san/iscsi/targets/' + target_name

        req = self.url + path

        self.LOG.debug("JovianDSS: check target [url]: {}".format(req))
        resp = self.rproxy.request('GET', req)

        if resp["error"] is not None and resp["code"] == 200:
            return False

        if "name" in resp["data"]:
            if resp["data"]["name"] == target_name:
                self.LOG.debug(
                    "JovianDSS: Request: {} SCCESS, taget found..".format(req))
                return True

        return False

    def create_target(self,
                      pool_name,
                      target_name,
                      use_chap=None,
                      allow_ip=None):
        """create_target
        POST
        /pools/<pool_name>/san/iscsi/targets

        :param pool_name:
        :param target_name:
        :param chap_cred:
        :param allow_ip:
        "allow_ip": [
                "192.168.2.30/0",
                "192.168.3.45"
            ],

        :return:
        """

        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets'
        req = self.url + path

        self.LOG.debug("JovianDSS: create target {} [url]: {}".format(
                                                            target_name, req))

        jdata = {"name": target_name}

        if use_chap is not None:
            jdata["incoming_users_active"] = True

        if allow_ip is not None:
            jdata["allow_ip"] = allow_ip

        resp = self.rproxy.request('POST', req, json_data=jdata)

        if resp["error"] is None and resp["code"] == 201:
            return

        # TODO: provide additional handling of different error cases
        raise jexc.JDSSRESTException(
            'Failed to create target {}.'.format(resp['error']['message']))

    def delete_target(self, pool_name, target_name):
        """delete_target
        DELETE
        pools/<pool_name>/san/iscsi/targets/<target_name>

        :param pool_name:
        :param target_name:
        :return:
        """

        if not self.is_target(pool_name, target_name):
            return

        path = self.api_path + '/pools/' + pool_name + \
            '/san/iscsi/targets/' + target_name
        req = self.url + path

        self.LOG.debug(
            "JovianDSS: delete target {}: {}".format(target_name, req))

        resp = self.rproxy.request('DELETE', req)

        if ((resp["code"] == 200) or
                (resp["code"] == 201) or
                (resp["code"] == 204)):
            self.LOG.debug(
                "JovianDSS: Target DELETE SUCCESS exiting. {}".format(req))
            return

        if (resp["code"] == 404) and \
                (resp["error"]["class"] == "werkzeug.exceptions.NotFound"):
            raise jexc.JDSSRESTResourceNotFoundException(
                                                        "Target do not exists.")

        raise jexc.JDSSRESTException('Failed to delete target.')

    def modify_target(self, pool_name, target_name, **kwargs):
        """modify_target
        PUT
        pools<pool_name>/san/iscsi/targets/<target_name>
        :param pool_name:
        :param target_name:
        :parameter
        {
            "name": "new_target_name",
            "active": True/False
            "incoming_users_active": True/False
            "outgoing_user": {
                            "password": "password",
                            "name": "mutual_user"
                            }
            "allow_ip": [
                "192.168.2.30/0",
                "192.168.3.45"
                    ],
            "deny_ip":  [
                "0.0.0.0/0"
                        ]
        }
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + \
            '/san/iscsi/targets/' + target_name

        req = self.url + path

        resp = self.rproxy.request('PUT', req, json_data=kwargs)

        if resp['error'] is not None or resp['code'] != 201:
            if resp['error']['message']:
                raise jexc.JDSSRESTException(resp['error']['message'])
            else:
                raise jexc.JDSSRESTException('Something wrong')

    def create_target_user(self, pool_name, target_name, chap_cred):
        """create_target_user
        POST
        pools<pool_name>/san/iscsi/targets/<target_name>/incoming-users

        :param pool_name:
        :param target_name:
        :param chap_cred:
        {
            "name": "target_user",
            "password": "3e21ewqdsacxz" --- 12 chars min
        }
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets/' + \
            target_name + "/incoming-users"
        req = self.url + path

        self.LOG.debug(
            "JovianDSS: User {} Pwd {} for target {}.".format(
                chap_cred["name"],
                chap_cred["password"],
                target_name))

        resp = self.rproxy.request('POST', req, json_data=chap_cred)

        if resp["error"] is None and \
                (resp["code"] == 200 or
                 resp["code"] == 201 or
                 resp["code"] == 204):
            return

        # TODO: provide additional handling of different error cases
        raise jexc.JDSSRESTException(
            'Failed to set target user {}.'.format(resp['error']['message']))

    def is_target_lun(self, pool_name, target_name, lun_name):
        """is_target_lun
        GET
        pools/<pool_name>/san/iscsi/targets/<target_name>/luns/<lun_name>

        :param pool_name:
        :param target_name:
        :param lun_name:
        :return: Bool
        """
        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets/' + \
            target_name + "/luns/" + lun_name
        req = self.url + path

        self.LOG.debug("JovianDSS: check target lun [url]: {}".format(req))
        resp = self.rproxy.request('GET', req)
        self.LOG.debug(
            "JovianDSS: Lun exists processing response: {}".format(resp))

        if resp["error"] is not None:
            return False

        if resp["code"] != 200:
            return False

        if resp["data"] is None:
            return False

        if "name" not in resp["data"]:
            return False

        if resp["data"]["name"] != lun_name:
            return False

        return True

    def attach_target_vol(self, pool_name, target_name, lun_name):
        """attach_target_vol
        POST
        pools/<pool_name>/san/iscsi/targets/<target_name>/luns

        :param pool_name:
        :param target_name:
        :param lun_name:
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets/' \
               + target_name + "/luns"
        req = self.url + path

        jbody = {"name": lun_name,}
        self.LOG.debug("JovianDSS: Atach lun {} to target {}: {}".format(
            lun_name, target_name, req))

        resp = self.rproxy.request('POST', req, json_data=jbody)

        if resp["error"] is None and resp["code"] == 201:
            return

        # TODO: provide additional handling of different error cases
        raise jexc.JDSSRESTException(
            'Failed to attach volume {}.'.format(resp['error']['message']))

    def detach_target_vol(self, pool_name, target_name, lun_name):
        """detach_target_vol
        DELETE
        pools/<pool_name>/san/iscsi/targets/<target_name>/luns/<lun_name>

        :param pool_name:
        :param target_name:
        :param lun_name:
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + '/san/iscsi/targets/' + \
            target_name + "/luns/" + lun_name

        req = self.url + path

        if not self.is_target_lun(pool_name, target_name, lun_name):
            return

        self.LOG.debug(
            "JovianDSS: Detach lun {} from target {} [url]: {}".format(
                                                                    lun_name,
                                                                    target_name,
                                                                    req))
        resp = self.rproxy.request('DELETE', req)

        if resp["code"] == 500 and \
                resp["error"]["class"] == "opene.san.iscsi.TargetNotFoundError":
            return

        if resp["code"] == 500 and \
                resp["error"]["class"] == \
                        "opene.san.iscsi.ZvolNotAssignedToTarget":
            return

        if resp["error"] is not None:
            raise jexc.JDSSRESTException(
                "Unable to detach lun: {}".format(resp["error"]['message']))

        if (resp["code"] == 200) or \
                (resp["code"] == 201) or \
                (resp["code"] == 204):
            return

        raise jexc.JDSSRESTException("Unable to detach lun.")

    def create_snapshot(self, pool_name, volume_name, snapshot_name):
        """create_snapshot
        POST
        /pools/<string:poolname>/volumes/<string:volumename>/snapshots

        :param pool_name:
        :param volume_name: source volume
        :param snapshot_name: snapshot name
        :return:
        """
        path = self.api_path + '/pools/' + pool_name + \
            '/volumes/' + volume_name + '/snapshots'

        req = self.url + path

        jbody = {
            'snapshot_name': snapshot_name
        }

        self.LOG.debug("JovianDSS: create snapshot [url]: %s" % req)

        resp = self.rproxy.request('POST', req, json_data=jbody)

        if (resp["error"] is None) and (
                (resp["code"] == 200) or
                (resp["code"] == 201) or
                (resp["code"] == 204)):
            return

        # TODO: provide additional handling of different error cases
        raise jexc.JDSSRESTException(
            'Failed to create snapshot {}.'.format(resp['error']['message']))

    def create_volume_from_snapshot(self, pool_name, volume_name,
                                    snapshot_name, original_vol_name):
        """create_volume_from_snapshot
        POST
        /pools/<string:poolname>/volumes/<string:volumename>/clone

        :param pool_name:
        :param volume_name: volume that is going to be created
        :param snapshot_name: slice of original volume
        :param original_vol_name: sample copy
        :return:
        """

        path = self.api_path + '/pools/' + pool_name + \
               '/volumes/' + original_vol_name + '/clone'

        jbody = {
            'name': volume_name,
            'snapshot': snapshot_name
        }

        req = self.url + path
        self.LOG.debug("JovianDSS: create volume from snapshot: {}".format(req))

        resp = self.rproxy.request('POST', req, json_data=jbody)

        if resp["error"] is None and (\
                (resp["code"] == 200) or
                (resp["code"] == 201) or
                (resp["code"] == 204)):
            return

        raise jexc.JDSSRESTException('unable to create volume')

    # TODO: implement this
    def is_snapshot(self, pool_name, volume_name, snapshot_name):
        return True

    def delete_snapshot(self,
                        pool_name,
                        volume_name,
                        snapshot_name,
                        recursively_children=False,
                        recursively_dependents=False,
                        force_umount=False):
        """delete_snapshot
        DELETE
        /pools/<string:poolname>/volumes/<string:volumename>/snapshots/
            <string:snapshotname>

        :param pool_name:
        :param volume_name: volume that snapshot belongs to
        :param snapshot_name: snapshot name
        :param recursively_children: boolean indicating if zfs should
            recursively destroy all children of resource, in case of snapshot
            remove all snapshots in descendant file system (default false).
        :param recursively_dependents: boolean indicating if zfs should
            recursively destroy all dependents, including cloned file systems
            outside the target hierarchy (default false).
        :param force_umount: boolean indicating if volume should be forced to
            umount (defualt false).
        :return:
        """

        if not self.is_snapshot(pool_name, volume_name, snapshot_name):
            return

        path = self.api_path + '/pools/' + pool_name + \
               '/volumes/' + volume_name + '/snapshots/' + snapshot_name

        req = self.url + path
        self.LOG.debug("JovianDSS: delete snapshot [url]: %s".format(req))

        jbody = {}
        if recursively_children is True:
            jbody['recursively_children'] = True

        if recursively_dependents is True:
            jbody['recursively_dependents'] = True

        if force_umount is True:
            jbody['force_umount'] = True

        resp = dict()
        if len(jbody) > 0:
            resp = self.rproxy.request('DELETE', req, json_data=jbody)
        else:
            resp = self.rproxy.request('DELETE', req)

        if ((resp["code"] == 200) or
                (resp["code"] == 201) or
                (resp["code"] == 204)):
            self.LOG.debug(
                "JovianDSS: Snapshot DELETE SUCCESS exiting. {}".format(req))
            return
        # TODO: analise error
        raise jexc.JDSSRESTException('Unable to delete snapshot')

    def get_snapshot(self, pool_name, volume_name, snapshot_name):
        """delete_snapshot
        DELETE
        /pools/<string:poolname>/volumes/<string:volumename>/
            snapshots/<string:snapshotname>

        :param pool_name:
        :param volume_name: that snapshot belongs to
        :param snapshot_name: snapshot name
        :return:
        {
            "data":
            [
                {
                    "referenced": "65536",
                    "name": "MySnapshot",
                    "defer_destroy": "off",
                    "userrefs": "0",
                    "primarycache": "all",
                    "type": "snapshot",
                    "creation": "2015-5-27 16:8:35",
                    "refcompressratio": "1.00x",
                    "compressratio": "1.00x",
                    "written": "65536",
                    "used": "0",
                    "clones": "",
                    "mlslabel": "none",
                    "secondarycache": "all"
                }
            ],
            "error": null
        }
        """
        path = self.api_path + '/pools/' + pool_name + \
               '/volumes/' + volume_name + '/snapshots/' + snapshot_name

        req = self.url + path
        self.LOG.debug(
            "JovianDSS: Get snapshot properties [url]: {}".format(req))

        resp = self.rproxy.request('GET', req)

        if resp["error"] is None and resp["code"] == 200:
            return resp["data"]

        raise jexc.JDSSRESTException('unable to get snapshot')

    def get_pool_stats(self, pool_name):
        """get_all_pool_fsproperties
        GET
        /pools/<string:poolname>

        :param pool_name:
        :return:
        {
          "data": {
            "available": "24433164288",
            "status": 24,
            "name": "Pool-0",
            "scan": {
              "errors": 0,
              "repaired": "0",
              "start_time": 1463476815,
              "state": "finished",
              "end_time": 1463476820,
              "type": "scrub"
            },
            "iostats": {
              "read": "0",
              "write": "0",
              "chksum": "0"
            },
            "vdevs": [
              {
                "name": "scsi-SSCST_BIOoWKF6TM0qafySQBUd1bb392e",
                "iostats": {
                  "read": "0",
                  "write": "0",
                  "chksum": "0"
                },
                "disks": [
                  {
                    "led": "off",
                    "name": "sdb",
                    "iostats": {
                      "read": "0",
                      "write": "0",
                      "chksum": "0"
                    },
                    "health": "ONLINE",
                    "sn": "d1bb392e",
                    "path": "pci-0000:04:00.0-scsi-0:0:0:0",
                    "model": "oWKF6TM0qafySQBU",
                    "id": "scsi-SSCST_BIOoWKF6TM0qafySQBUd1bb392e",
                    "size": 30064771072
                  }
                ],
                "health": "ONLINE",
                "vdev_replacings": [],
                "vdev_spares": [],
                "type": ""
              }
            ],
            "health": "ONLINE",
            "operation": "none",
            "id": "11612982948930769833",
            "size": "29796335616"
          },
          "error": null
        }
        """

        path = self.api_path + '/pools/' + pool_name
        req = self.url + path
        self.LOG.debug("JovianDSS: get pool fsprops [url]: {}".format(req))

        resp = self.rproxy.request('GET', req)
        if resp["error"] is None and resp["code"] == 200:
            return resp["data"]

        raise jexc.JDSSRESTException('unable to pool info')
