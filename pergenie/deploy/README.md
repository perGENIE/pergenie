# Deployment scripts for hosting `perGENIE` server


## Getting Started

1\. Install `VirtualBox` & `Vagrant`.

2\. Install `Ansible`.

3\. Build the VM and deploy:

```
$ vagrant up
```


## Notes

- For production use, replace `Vagrant` to actual servers.
- Define servers in `playbook/hosts`, and run `Ansible` playbooks against remote servers:

```
$ ansible-playbook playbook/site.yml -i playbook/hosts --ask-become-pass
```

See details in `Vagrantfile` and `playbook`.


## Versions

|                        | version          |
|------------------------|------------------|
| CentOS                 | 6.7              |
| Python                 | 2.7              |
| PostgreSQL             | 9.4              |
| RabbitMQ               | 3.5              |
| Apache httpd           | 2.2              |
