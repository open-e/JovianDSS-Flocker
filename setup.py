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

import codecs
from setuptools import setup, find_packages

with codecs.open('DESCRIPTION.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='joviandss_flocker_driver',
    version='0.9',
    description='Open-E JovianDSS Plugin for ClusterHQ/Flocker',
    long_description=long_description,
    author='Andrei Perepiolkin',
    author_email='andrei.perepiolkin@open-e.com',

    keywords='docker, flocker, plugin, python',
    packages=find_packages(exclude=['test*']),
    install_requires=['uuid'],
    data_files=[('/etc/flocker/', [])]
)
