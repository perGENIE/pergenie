# Deploy scripts for hosting `perGENIE`


## Getting started for staging env

1\. Install `VirtualBox`, `Vagrant`, and `Ansible`.

2\. Configure variables in playbook:

```
$ ${EDITOR} playbook/group_vars/staging  # e.g. playbook/group_vars/staging.example
```

3\. Build VM and deploy:

```
$ vagrant up
```

Once VM is up, to rollout pergenie application:

```
$ ANSIBLE_TAGS=rollout vagrant provision
```

## For production env

1\. Define production servers in `playbook/hosts`:

```
$ ${EDITOR} playbook/hosts  # e.g. playbook/hosts.example
```

2\. Run `Ansible` playbooks against remote servers:

```
$ ansible-playbook playbook/site.yml -i playbook/hosts --ask-become-pass
```

See details in `Vagrantfile` and `playbook`.


## Software versions in playbook

- CentOS 6.7

|                        | version          |                   |
|------------------------|------------------|-------------------|
| Python                 | 2.7              | build from source |
| PostgreSQL             | 9.4              | yum with rpm repo |
| RabbitMQ               | 3.5              | yum with rpm repo |
| Apache httpd           | 2.2              | yum               |
