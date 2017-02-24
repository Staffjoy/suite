# -*- mode: ruby -*-
# vi: set ft=ruby :

def fail_with_message(msg)
  fail Vagrant::Errors::VagrantError.new, msg
end

ip = '192.168.70.70'

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "trusty-amd64"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
  config.vm.network :private_network, ip: ip
  if Vagrant.has_plugin? 'vagrant-hostmanager'
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
    config.hostmanager.aliases = [
      'suite.local',
    ]
  else
    fail_with_message "vagrant-hostmanager missing, please install the plugin with this command:\nvagrant plugin install vagrant-hostmanager"
  end

  if !Vagrant.has_plugin? 'vagrant-vbguest'
    fail_with_message "vagrant-vbgues missing, please install the plugin with this command:\nvagrant plugin install vagrant-vbguest"
  end

  config.vm.synced_folder ".", "/vagrant"
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "2000"]
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    # Sync NTP every 10 seconds to avoid drift
    vb.customize ["guestproperty", "set", :id, "/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold", 10000]
  end

  config.vm.provision "shell", path: "vagrant.sh"
end
