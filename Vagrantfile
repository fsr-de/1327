# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Base box to build off, and download URL for when it doesn't exist on the user's system already
  config.vm.box = "puppetlabs/ubuntu-14.04-64-puppet"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine.
  config.vm.network :forwarded_port, guest: 80, host: 8000

  config.vm.provider :virtualbox do |vb, override|
    vb.customize ["modifyvm", :id, "--memory", "1024"]

    override.vm.box_url = "https://vagrantcloud.com/puppetlabs/boxes/ubuntu-14.04-64-puppet/versions/3/providers/virtualbox.box"
  end

  config.vm.provision :puppet do |puppet|
    puppet.module_path = "deployment/modules"
    puppet.manifests_path = "deployment"
    puppet.manifest_file = "site.pp"
  end
end
