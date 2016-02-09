# Deploy scripts for hosting `perGENIE`


## Setup for staging env

1\. Install `VirtualBox`, `Vagrant`, and `Ansible`.

2\. Configure variables in playbook:

```
$ ${EDITOR} playbook/group_vars/staging  # e.g. playbook/group_vars/staging.example
```

3\. Build VM and deploy:

```
$ vagrant up
```

**NOTE:** Once VM is up, you can rollout pergenie application by:

```
$ ANSIBLE_TAGS=rollout vagrant provision
```

4\. Edit /etc/hosts on localhost

Add following line to /etc/hosts on localhost:

```
127.0.0.1 staging.pergenie.org
```

5\. You can browse perGENIE at following url:

```
$ https://staging.pergenie.org:8443/
```


## Setup for production env

1\. Define production servers in `playbook/hosts`:

```
$ ${EDITOR} playbook/hosts  # e.g. playbook/hosts.example
```

2\. Run `Ansible` playbooks against remote servers:

```
$ ansible-playbook playbook/site.yml -i playbook/hosts --ask-become-pass
```

**NOTE:** See details in `Vagrantfile` and `playbook`.


## Software versions in playbook

- CentOS 7.2

|                        | version          |                            |
|------------------------|------------------|----------------------------|
| Python                 | 2.7              | yum default                |
| PostgreSQL             | 9.4              | yum with official rpm repo |
| RabbitMQ               | 3.6              | yum with official rpm repo |
| Apache httpd           | 2.4              | yum default                |
