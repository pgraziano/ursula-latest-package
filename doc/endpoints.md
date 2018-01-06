
Endpoints
=========

For this document we are including both OpenStack API services and internal
dependencies services like RabbitMQ and MySQL in our definition of endpoints.

There are three IP addresses we use for endpoints:

1. Each controller's internal "undercloud" IP address.
2. The floating internal "undercloud" IP address shared by the controllers.
3. The floating external IP address shared by the controllers.

Since we are already running HAProxy to terminate SSL and provide high
availability for external API requests, we decided to leverage this to protect
against API service failures on the controller which has the floating IP and
connect to HAProxy over SSL for internal API requests. This avoids the
complexity of having third port for each API service for HAProxy listen on for
plain text request, or binding HAProxy and API services each to specific IPs.

Since we are using SSL for internal communication, clients require connections
via hostname rather than IP to allow certificate validation. Rather than using
split-horizon DNS or similar technology to allow the internal API clients to
connect to the internal floating IP, we routed the internal API clients to the
same public address as the external clients. One disadvantage from using this
NAT is the loss of logging information regarding the originating node of the API
request.


| Service        | Clients  | Protocol | Port  | IP                     |
| -------------- | -------- | -------- | ----- | ---------------------- |
| Horizon        | haproxy  | HTTP     | 8080  | controller internal IP |
| Horizon        | public   | HTTPS    | 443   | external floating IP   |
| MySQL          | internal | mysql    | 3306  | internal floating IP   |
| MongoDB        | internal | mongodb  | 27017 | internal floating IP   |
| RabbitMQ       | internal | rabbitmq | 5672  | internal floating IP   |
| Memcached      | internal | memcache | 11211 | controller internal IP |
| Keystone       | haproxy  | HTTP     | 5001  | controller internal IP |
| Keystone       | internal | HTTPS    | 5000  | external floating IP   |
| Keystone       | public   | HTTPS    | 5000  | external floating IP   |
| Keystone-admin | haproxy  | HTTP     | 35358 | controller internal IP |
| Keystone-admin | internal | HTTPS    | 35357 | external floating IP   |
| Keystone-admin | public   | HTTPS    | 35357 | external floating IP   |
| Nova           | haproxy  | HTTP     | 9774  | controller internal IP |
| Nova           | internal | HTTPS    | 8774  | external floating IP   |
| Nova           | public   | HTTPS    | 8774  | external floating IP   |
| Nova - noVNC   | internal | HTTP     | 6081  | controller internal IP |
| Nova - noVNC   | public   | HTTPS    | 6080  | external floating IP   |
| Neutron        | haproxy  | HTTP     | 9797  | controller internal IP |
| Neutron        | internal | HTTPS    | 9696  | external floating IP   |
| Neutron        | public   | HTTPS    | 9696  | external floating IP   |
| Glance         | haproxy  | HTTP     | 9393  | controller internal IP |
| Glance         | internal | HTTPS    | 9292  | external floating IP   |
| Glance         | public   | HTTPS    | 9292  | external floating IP   |
| Heat           | haproxy  | HTTP     | 8004  | controller internal IP |
| Heat           | internal | HTTPS    | 8005  | external floating IP   |
| Heat           | public   | HTTPS    | 8005  | external floating IP   |
| Heat CFN       | haproxy  | HTTP     | 8000  | controller internal IP |
| Heat CFN       | internal | HTTPS    | 8001  | external floating IP   |
| Heat CFN       | public   | HTTPS    | 8001  | external floating IP   |
| Ceilometer     | haproxy  | HTTP     | 8777  | controller internal IP |
| Ceilometer     | internal | HTTPS    | 9777  | external floating IP   |
| Ceilometer     | public   | HTTPS    | 9777  | external floating IP   |
| Ironic-api     | haproxy  | HTTP     | 6385  | controller internal IP |
| Ironic-api     | internal | HTTPS    | 6384  | external floating IP   |
| Ironic-api     | public   | HTTPS    | 6384  | external floating IP   |
