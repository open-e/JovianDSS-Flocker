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

from flocker.node import BackendDescription, DeployerType
from jdss_driver import JovianDSSBlockDeviceAPI

def api_factory(cluster_id, **kwargs):
    return JovianDSSBlockDeviceAPI(cluster_id=cluster_id, conf_file=kwargs.get(
        u"joviandss_conf_file"))

FLOCKER_BACKEND = BackendDescription(
    name=u"joviandss_flocker_driver",
    needs_reactor=False, needs_cluster_id=True,
    api_factory=api_factory, deployer_type=DeployerType.block)
