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


from flocker.node.agents.blockdevice import (
    VolumeException, AlreadyAttachedVolume,
    UnknownVolume, UnattachedVolume,
    IBlockDeviceAPI,
    BlockDeviceVolume
)

import yaml
from uuid import UUID
from zope.interface import implementer
from twisted.python.filepath import FilePath

from jovian_common import rest
from jovian_common import jdss_common as jcom
from jovian_common import exception as jexc
from log import LOG


@implementer(IBlockDeviceAPI)
class JovianDSSBlockDeviceAPI(object):
    """
    Jovian driver implemented ``IBlockDeviceAPI``.
    """

    def __init__(self, cluster_id, conf_file):
        """
        :param conf_file: The path of JDSS config file.
        :returns: A ``BlockDeviceVolume``.
        """
        LOG.debug("JDSS block device init")
        config = yaml.load(open(str(conf_file)))
        self._cluster_id = cluster_id
        self.rest = rest.JovianRESTAPI(LOG, config)
        self._compute_instance_id = config.get('flocker_instance_id',
                                               jcom.name_for_node())
        self._allocation_unit = config.get('allocation_unit', 1024**2)
        self.host = config.get('jovian_host')
        self.Pool = config.get('jovian_pool', 'Pool-0')
        if not self.rest.is_pool_exists(self.Pool):
            LOG.error("Pool {} isn't exist".format(self.Pool))
            raise jexc.UnknownPool(self.Pool)
        self.target_port = config.get('jovian_iscsi_target_portal_port', 3260)
        self.jovian_target_prefix = config.get('jovian_target_prefix',
                                               'iqn.2016-10.com.open-e.iscsi')
        if self.jovian_target_prefix[-1] != ':':
            self.jovian_target_prefix += ':'

        LOG.debug("Finish JDSS block device init")

    def _cleanup(self):
        """
        Remove all volumes
        """
        targets = [targ['name'] for targ in self.rest.get_targets(self.Pool)]
        volumes = self.list_volumes()
        for volume in volumes:
            for target in targets:
                if volume.blockdevice_id in target:
                    try:
                        self.rest.delete_target(self.Pool, target)
                    except Exception:
                        pass
            self.destroy_volume(volume.blockdevice_id)
        jcom.iscsiadm_logoutall_targets()

    def allocation_unit(self):
        """
        The size, in bytes up to which ``IDeployer`` will round volume
        sizes before calling ``IBlockDeviceAPI.create_volume``.

        :returns: ``int``
        """
        LOG.debug("Call allocation_unit = {}".format(self._allocation_unit))
        return self._allocation_unit

    def compute_instance_id(self):
        """
        Get an identifier for this node.

        This will be compared against ``BlockDeviceVolume.attached_to``
        to determine which volumes are locally attached and it will be used
        with ``attach_volume`` to locally attach volumes.

        :returns: A ``unicode`` object giving a provider-specific node
            identifier which identifies the node where the method is run.
        """

        LOG.debug("Call compute_instance_id = %s" % self._compute_instance_id)
        return unicode(self._compute_instance_id)

    def create_volume(self, dataset_id, size):
        """
        Create a new volume.

        When called by ``IDeployer``, the supplied size will be
        rounded up to the nearest ``IBlockDeviceAPI.allocation_unit()``

        :param UUID dataset_id: The Flocker dataset ID of the dataset on this
            volume.
        :param int size: The size of the new volume in bytes.
        :returns: A ``BlockDeviceVolume``.
        """
        LOG.debug("Call create_volume, dataset_id=%s, size=%d"
                 % (dataset_id, size))

        name = str(self._cluster_id) + '.' + str(dataset_id)
        try:
            self.rest.create_lun(self.Pool, name, int(size))
        except jexc.JDSSRESTException as error_message:
            LOG.debug(error_message)
            raise VolumeException(error_message)

        volume = BlockDeviceVolume(
            size=int(size),
            attached_to=None,
            dataset_id=dataset_id,
            blockdevice_id=unicode(name)
        )
        return volume

    def destroy_volume(self, blockdevice_id):
        """
        Destroy an existing volume.

        :param unicode blockdevice_id: The unique identifier for the volume to
            destroy.
        """
        LOG.debug('Call destroy_volume, blockdevice_id=%s' % blockdevice_id)

        if not self.rest.is_lun(self.Pool, blockdevice_id):
            raise UnknownVolume(blockdevice_id)

        target_name = '{}{}.{}'.format(self.jovian_target_prefix,
                                       blockdevice_id,
                                       self._compute_instance_id)
        if self.rest.is_target(self.Pool, target_name):
            if self.rest.is_target_lun(self.Pool, target_name, blockdevice_id):
                jcom.iscsiadm_logout_target(target_name, self.host,
                                            self.target_port)
                self.rest.detach_target_vol(self.Pool, target_name,
                                            blockdevice_id)
            self.rest.delete_target(self.Pool, target_name)
        self.rest.delete_lun(self.Pool, str(blockdevice_id))

    def attach_volume(self, blockdevice_id, attach_to):
        """
        Attach ``blockdevice_id`` to the node indicated by ``attach_to``.

        :param unicode blockdevice_id: The unique identifier for the block
            device being attached.
        :param unicode attach_to: An identifier like the one returned by the
            ``compute_instance_id`` method indicating the node to which to
            attach the volume.
        :returns: A ``BlockDeviceVolume`` with a ``attached_to`` attribute set
            to ``attach_to``.
        """
        LOG.debug("Call attach_volume blockdevice_id=%s, attach_to=%s"
                 % (blockdevice_id, attach_to))

        if not self.rest.is_lun(self.Pool, blockdevice_id):
            raise UnknownVolume(blockdevice_id)

        vol_info = self.rest.get_lun(self.Pool, blockdevice_id)

        target_name = '{}{}.{}'.format(self.jovian_target_prefix,
                                        blockdevice_id, attach_to)

        targets = [targ['name'] for targ in self.rest.get_targets(self.Pool)]
        for target in targets:
            if blockdevice_id in target and target_name != target and \
                    self.rest.is_target_lun(self.Pool, target, blockdevice_id):
                raise AlreadyAttachedVolume(blockdevice_id)
            elif target_name == target and jcom.check_target_by_path(
                                                                target_name):
                raise AlreadyAttachedVolume(blockdevice_id)

        if not self.rest.is_target(self.Pool, target_name):
            self.rest.create_target(self.Pool, target_name)

        if not self.rest.is_target_lun(self.Pool, target_name, blockdevice_id):
            try:
                self.rest.attach_target_vol(self.Pool, target_name,
                                            blockdevice_id)
                if not self.rest.is_target_lun(self.Pool, target_name,
                                               blockdevice_id):
                    self.rest.delete_target(self.Pool, target_name)
                    raise VolumeException(blockdevice_id)
            except jexc.JDSSRESTException as error_message:
                LOG.debug(error_message)
                raise VolumeException(error_message)

        if not jcom.check_target_by_path(target_name):
            jcom.iscsiadm_discovery_target(target_name, self.host)
            jcom.iscsiadm_login_target(target_name, self.host, self.target_port)
        else:
            raise AlreadyAttachedVolume(blockdevice_id)

        jcom.check_local_disck_by_path()

        attached_volume = BlockDeviceVolume(
            size=int(vol_info['volsize']),
            attached_to=attach_to,
            dataset_id=UUID('{}'.format(blockdevice_id.split('.')[-1])),
            blockdevice_id=blockdevice_id)
        return attached_volume

    def detach_volume(self, blockdevice_id):
        """
        Detach ``blockdevice_id`` from whatever host it is attached to.

        :param unicode blockdevice_id: The unique identifier for the block
            device being detached.
        """

        LOG.debug("Call detach_volume blockdevice_id=%s" % blockdevice_id)

        if not self.rest.is_lun(self.Pool, blockdevice_id):
            raise UnknownVolume(blockdevice_id)

        target_name = '{}{}.{}'.format(self.jovian_target_prefix,
                                       blockdevice_id,
                                       self._compute_instance_id)

        jcom.iscsiadm_logout_target(target_name, self.host, self.target_port)

        if not self.rest.is_target(self.Pool, target_name):
            raise UnattachedVolume(blockdevice_id)
        elif not self.rest.is_target_lun(self.Pool, target_name,
                                         blockdevice_id):
            self.rest.delete_target(self.Pool, target_name)
            raise UnattachedVolume(blockdevice_id)

        self.rest.detach_target_vol(self.Pool, target_name,
                                    blockdevice_id)
        self.rest.delete_target(self.Pool, target_name)
        jcom.rm_local_dir('/flocker/{}/'.format(blockdevice_id))

    def list_volumes(self):
        """
        List all the block devices available via the back end API.

        :returns: A ``list`` of ``BlockDeviceVolume``s.
        """
        LOG.debug("Call list_volumes")

        volumes = []
        vols = self.rest.get_luns(self.Pool)
        targets = [targ['name'] for targ in self.rest.get_targets(self.Pool)]
        for volume in vols:
            if str(self._cluster_id) in volume['name']:
                for targ_name in targets:
                    if volume['name'] in targ_name:
                        if self.rest.is_target_lun(self.Pool, targ_name,
                                                   volume['name']):
                            volumes.append(BlockDeviceVolume(
                                size=int(volume['volsize']),
                                attached_to=targ_name.split(':')[1].split(
                                                                     '.')[-1],
                                dataset_id=UUID(volume['name'].split('.')[-1]),
                                blockdevice_id=unicode(volume['name'])))
                            break
                        else:
                            try:
                                self.rest.delete_target(self.Pool, targ_name)
                            except Exception as error_message:
                                LOG.debug(error_message)
                else:
                    volumes.append(BlockDeviceVolume(
                        size=int(volume['volsize']),
                        attached_to=None,
                        dataset_id=UUID(volume['name'].split('.')[1]),
                        blockdevice_id=unicode(volume['name'])))

        LOG.debug('Volumes: {}'.format(volumes))
        return volumes

    def get_device_path(self, blockdevice_id):
        """
        Return the device path that has been allocated to the block device on
        the host to which it is currently attached.

        :param unicode blockdevice_id: The unique identifier for the block
            device.
        :returns: A ``FilePath`` for the device.
        """

        LOG.debug("Call get_device_path blockdevice_id=%s" % blockdevice_id)

        if not self.rest.is_lun(self.Pool, blockdevice_id):
            raise UnknownVolume(blockdevice_id)

        target_name = '{}{}.{}'.format(self.jovian_target_prefix,
                                        blockdevice_id,
                                        self._compute_instance_id)

        if not self.rest.is_target(self.Pool, target_name):
            raise UnattachedVolume(blockdevice_id)

        path = jcom.get_local_disk_path(target_name)
        if path:
            LOG.debug('device_path was found: {}'.format(path))
            return FilePath('/dev/' + str(path))

        return None
