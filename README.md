<center>![alt tag](https://avatars1.githubusercontent.com/u/4292978?v=3&s=200) </center>
	 

# <center> Flocker-driver</center>


## Description

This repository contains source files for the Open-E JovianDSS ClusterHQ/flocker driver/plugin.


## Installation

To make Open-E JovianDSS work properly with your Flocker base environment you have to install it on every Agent node.

Ensure that you have lsscsi and iscsi-initiator-utils installed. 
On the rpm based systems you can install them by running:

### Install driver and tools

```bash
yum -y install lsscsi
yum -y install iscsi-initiator-utils
```

Install latest code from repository:

```bash
sudo $PATH_TO_PIP/pip install git+https://github.com/open-e/Flocker-driver.git
```



### Configure driver

Create and edit the joviandss_flocker_conf.yml config file. It is expected to be at "/etc/flocker/joviandss_flocker_conf.yml" 
```bash
"jovian_host" : "192.168.0.128"
"jovian_rest_protocol" : "https"
"jovian_rest_port" : 82
"jovian_user" : "admin"
"jovian_password" : "admin"
"jovian_iscsi_target_portal_port" : 3260
"jovian_target_prefix" : "iqn.2016-04.com.open-e:"
"jovian_pool" : "Pool-0"
"jovian_rest_send_repeats" : 3
"flocker_allocation_unit" : 1073741824
"flocker_instance_id" : "node1"
```

| Property   	|  Default value  	|  Description 	|
|:----------:	|:-------------:	|:------:	|
| jovian\_host   | 	               | IP address of the JovianDSS | 
| jovian\_rest\_protocol 	| https | Protocol to connect to JovianDSS. Https must be enabled on the JovianDSS site [1].  |
| jovian\_rest\_port | 82               | Must be set according to the settings in [1] |
| jovian\_user       | admin            | Must be set according to the settings in [1] |
| jovian\_password   | admin            | Must be set according to the settings in [1] |
| jovian\_iscsi\_target\_portal\_port | 3260 | Port for iSCSI connection               |
| jovian\_target\_prefix | iqn.2016-04.com.open-e: | Prefix that will be used to form target name for volume |
| jovian\_pool | Pool-0 | Pool name that is going to be used to store volumes. Must be created in [2] |
| jovian\_rest\_send\_repeats | 3 | Number of times that CinderDriver will provide to send REST request. |
| flocker\_allocation\_unit | 1073741824 | Set for the Flocker minimal allocation unit. |
| flocker\_instance\_id |   | Unique text string that can contain [0-9] [a-z] and '-'. Should not be *MORE* longer then 36 symbols |



[1] Can be enabled by going to: JovianDSS Web interface/System Settings/REST Access 

[2] [Can be created by going to JovianDSS Web interface/Storage](https://www.open-e.com/site_media/download/documents/Open-E-JovianDSS-High-Availability-Cluster-Step-by-Step.pdf)

Create and edit flocker agent config file agent.yml. It is expected to be at "/etc/flocker/agent.yml" 

```bash
version: 1
control-service:
   hostname: "192.168.0.4"
dataset:
    backend: "jovian_dss_driver"
    joviandss_conf_file: "/etc/flocker/flocker_jovian_dss_conf.yml"
```

| Property   	|  Description 	|
|:----------:	|  :------:	|
| hostname   | 	IP address of the host with control service | 
| backend 	| name of the driver you are going yo use ---  joviandss_driver  |
| joviandss_conf_file  | file that stores configs for JovianDSS driver --- joviandss_flocker_conf.yml  |


### ReStart services

Ensure that appropriate services is running:

```bash
systemctl stop flocker-dataset-agent
systemctl enable flocker-dataset-agent
systemctl start flocker-dataset-agent

systemctl stop flocker-container-agent
systemctl enable flocker-container-agent
systemctl start flocker-container-agent
```

## Example of deployment
<center>![alt tag](https://github.com/AndreiPerepiolkin/Diagrams/blob/master/Flocker_with_JovianDSS.png?raw=true) </center>


## Testing

Now your should have your Flocker agent able to use JovianDSS driver.

Run command:
```bash
flockerctl --control-service=192.168.0.4 list
```
You will get:
```bash
DATASET   SIZE   METADATA   STATUS   SERVER 
```
This means that you have no volumes created.

Run this command to see available nodes:
```bash
flockerctl --control-service=192.168.0.4 list-nodes
```

You will get something like this:
```bash
SERVER     ADDRESS
43a06d55   192.168.0.4 
430e9391   192.168.0.5
```
Run this command to create volume with size 1 Gigabyte
```bash
flockerctl --control-service=192.168.0.4 create -n 43a06d55 -s 1G
```
Now you can check status by running:
```bash
flockerctl --control-service=192.168.0.4 list
```
You will get something like this:
```bash
DATASET                                SIZE    METADATA   STATUS         SERVER
bef1f5c1-d8ef-4351-b495-2f03a9cae6ad   1.00G              attached ✅   43a06d55 (192.168.0.4) 
```

Now you can check if you can 'move' volume from one node to another. Run command:
```bash
flockerctl --control-service=192.168.0.4 move -d 5030bb09-fe05-4285-af5c-911e64412071 -t 430e9391
```
This command will move volume 5030bb09-fe05-4285-af5c-911e64412071 to the node with ID 430e9391.

Now you can check updated status by running:
```bash
flockerctl --control-service=192.168.0.4 list
```

The response should looks like:
```bash
DATASET                                SIZE    METADATA   STATUS         SERVER 
5030bb09-fe05-4285-af5c-911e64412071   1.00G              attached     430e9391 (192.168.0.5) 
```

Now, if you are not interested in the volume, it can be easily removed by calling:
```bash
flockerctl --control-service=192.168.0.4 destroy -d 5030bb09-fe05-4285-af5c-911e64412071
```

Now you can check updated status by running:
```bash
flockerctl --control-service=192.168.0.4 list
```

The response should looks like:
```bash
DATASET                                SIZE    METADATA   STATUS         SERVER 

```

Driver is working. 


In other cases please check that your Flocker deployment is correct.
If you believe that there is a problem in driver please contact me at andrei.perepolkin@open-e.com.

## License

    Copyright (c) 2016 Open-E, Inc.
    All Rights Reserved.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

## Feedback

Please address problems and proposals to andrei.perepiolkin@open-e.com

