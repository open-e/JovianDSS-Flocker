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

from flocker.node.agents.test.test_blockdevice import (
                                                    make_iblockdeviceapi_tests)
from uuid import uuid4

from jdss_driver import JovianDSSBlockDeviceAPI

def api_factory(test_case):
    jdss = JovianDSSBlockDeviceAPI(uuid4(),
                                   u"/etc/flocker/joviandss_conf_file.yml")
    test_case.addCleanup(jdss._cleanup)
    return jdss

class JovianDSSBlockDeviceAPITests(
        make_iblockdeviceapi_tests(
            blockdevice_api_factory=api_factory,
            minimum_allocatable_size=1024**2,
            device_allocation_unit=1024**2,
            unknown_blockdevice_id_factory=lambda test: unicode(uuid4())
        )
):
    """
    Interface adherence Tests for ``JovianDSSBlockDeviceAPI``
    """
