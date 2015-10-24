# Deployment scripts for hosting `perGENIE` server.


## Requirements

- `VirtualBox` & `Vagrant`
- `Ansible`


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
