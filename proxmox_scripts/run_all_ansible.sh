ansible-playbook -i inventory.ini dev-base.yml --ask-vault-pass
ansible-playbook -i inventory.ini admin-base.yml
ansible-playbook -i inventory.ini db-base.yml
ansible-playbook -i inventory.ini fs-base.yml
