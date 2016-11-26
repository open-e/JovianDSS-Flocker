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

from time import gmtime, strftime, time

from . import exception as jexc


max_volume_name_size = 32

def command(cmd):
    import os
    pipe = os.popen('{ ' + cmd + '; } 2>&1', 'r')
    text = pipe.read()
    pipe.close()
    return text.strip()

def name_for_node():
    return command('uname -n').lower().replace('.', '').\
                                                        replace(':', '')


def check_local_disck_by_path():
    res = command('ls -l /dev/disk/by-path')
    t0 = time()
    while 'No such file or directory' in res:
        res = command('ls -l /dev/disk/by-path')
        t = time()
        if t - t0 > 300:
            res = command('ls -l /dev/disk/by-path')
            if 'No such file or directory' in res:
                raise jexc.JDSSException(res)


def get_local_disk_path(target_name):
    t0 = time()
    while True:
        res = command('ls -l /dev/disk/by-path')
        disks = res.replace(' ', '').split()

        for disk in disks:
            if target_name in disk:
                path = disk[-3:]
                fdisk = command('fdisk -l')
                if path in fdisk:
                    return path

        t = time()
        if t - t0 > 15:
            break


def check_target_by_path(target_name):
    path = get_local_disk_path(target_name)

    if path is not None:
        return True
    else:
        return False


def iscsiadm_discovery_target(target_name, host):
    res = command('iscsiadm -m discovery -t st -p {}'.format(host))
    t0 = time()
    while target_name not in res:
        res = command('iscsiadm -m discovery -t st -p {}'.format(host))
        t = time()
        if t - t0 > 300:
            res = command('iscsiadm -m discovery -t st -p {}'.format(host))
            if target_name not in res:
                raise jexc.JDSSException(
                    'target {} is not discovered'.format(target_name))


def iscsiadm_login_target(target_name, host, target_port):
    res = command('iscsiadm -m node -T {} -p {}:{} --login'.format(
                                               target_name, host, target_port))
    if 'successful' not in res and not check_target_by_path(target_name):
        raise jexc.JDSSException('target {} is not attached. {}'.
                                 format(target_name, res))


def iscsiadm_logout_target(target_name, host, target_port):
    command('iscsiadm -m node -u -T {} -p {}:{} --logout'.
            format(target_name, host, target_port))


def iscsiadm_logoutall_targets():
    command('iscsiadm -m node --logoutall=all')


def rm_local_dir(path):
    command('rm -Rf {}'.format(path))


def cinder_name_2_id(name_str):
    volume_prefix = "volume-"

    if len(volume_prefix) >= name_str or\
            volume_prefix != name_str[0:len(volume_prefix)]:
        raise jexc.JDSSIncorrectVolumeNameException("Unexpected volume name.")

    id_str = name_str[len(volume_prefix):]
    id_str = id_str.replace("-", "")

    if len(id_str) > max_volume_name_size:
        raise jexc.JDSSIncorrectVolumeNameException("Unexpected volume name.")

    return id_str


def cinder_name_id_2_id(name_str):

    id_str = name_str.replace("-", "")

    if len(id_str) > max_volume_name_size:

        raise jexc.JDSSIncorrectVolumeNameException("Unexpected volume name.")

    return id_str


def get_year_month():
    return strftime("%Y-%m", gmtime())


def get_jprefix():
    return "iqn.2015-05:"


def origin_snapshot(origin_str):
    return origin_str.split("@")[1]


def origin_volume(pool, origin_str):
    return origin_str.split("@")[0].split(pool + "/")[1]
