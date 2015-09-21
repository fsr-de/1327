# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.7.4"

Vagrant.configure("2") do |config|
  # Base box to build off, and download URL for when it doesn't exist on the user's system already
  config.vm.box = "puppetlabs/ubuntu-14.04-64-puppet"
  config.vm.box_version = "= 1.0.2"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine.
  config.vm.network :forwarded_port, guest: 80, host: 8000
  config.vm.network :forwarded_port, guest: 8000, host: 8080

  config.vm.provision :puppet do |puppet|
    puppet.environment_path = "deployment"
    puppet.environment = "development"
  end
end
