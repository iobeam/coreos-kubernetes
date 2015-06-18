# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

$coreos_update_channel = "stable"
NUM_NODES = ENV['NUM_NODES'] || 2
$coreos_name_prefix = "node"
$coreos_vm_gui = false

$coreos_master_vm_memory = 512
$coreos_master_vm_cpus = 1

$coreos_node_vm_memory = 2048
$coreos_node_vm_cpus = 1

# Use old vb_xxx config variables when set
def coreos_vm_gui
  $vb_gui.nil? ? $coreos_vm_gui : $vb_gui
end

def coreos_vm_memory(i)

  if i == 1 then
    $vb_memory.nil? ? $coreos_master_vm_memory : $vb_memory
  else
    $vb_memory.nil? ? $coreos_node_vm_memory : $vb_memory
  end
end

def coreos_vm_cpus(i)
  if i == 1 then 
    $vb_cpus.nil? ? $coreos_master_vm_cpus : $vb_cpus
  else
    $vb_cpus.nil? ? $coreos_node_vm_cpus : $vb_cpus
  end
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  
  # always use Vagrants insecure key
  config.ssh.insert_key = false
  
  config.vm.provider :virtualbox do |v|
    # On VirtualBox, we don't have guest additions or a functional vboxsf
    # in CoreOS, so tell Vagrant that so it can be smarter.
    v.check_guest_additions = false
    v.functional_vboxsf     = false
  end

  # plugin conflict
  if Vagrant.has_plugin?("vagrant-vbguest") then
    config.vbguest.auto_update = false
  end

  config.ssh.forward_agent = true

  # Launch Core OS cluster.
  config.vm.box = "coreos-%s" % $coreos_update_channel
  config.vm.box_version = ">= 308.0.1"
  config.vm.box_url = "http://%s.release.core-os.net/amd64-usr/current/coreos_production_vagrant.json" % $coreos_update_channel

  
  # Generate cloud-config files (defaults to /tmp/)
  if ARGV.first == "up"
    system( "./make_cloud_config.py" )
  end
     
  (1..(NUM_NODES.to_i + 1)).each do |i|

    if i == 1
      hostname = "master"
    else
      hostname = "%s-%02d" % [$coreos_name_prefix, (i - 1)]      
    end
    config.vm.define vm_name = hostname do |machine|
      machine.vm.hostname = vm_name
      
      if $enable_serial_logging
        logdir = File.join(File.dirname(__FILE__), "log")
        FileUtils.mkdir_p(logdir)

        serialFile = File.join(logdir, "%s-serial.txt" % vm_name)
        FileUtils.touch(serialFile)

        machine.vm.provider :virtualbox do |vb, override|
          vb.customize ["modifyvm", :id, "--uart1", "0x3F8", "4"]
          vb.customize ["modifyvm", :id, "--uartmode1", serialFile]
        end
      end

      if $expose_docker_tcp
        machine.vm.network "forwarded_port", guest: 2375, host: ($expose_docker_tcp + i - 1), auto_correct: true
      end

      machine.vm.provider :virtualbox do |vb|
        vb.gui = coreos_vm_gui
        vb.memory = coreos_vm_memory(i)
        vb.cpus = coreos_vm_cpus(i)
      end

      ip = "172.17.8.#{i+100}"
      machine.vm.network :private_network, ip: ip

      # Uncomment below to enable NFS for sharing the host machine into the coreos-vagrant VM.
      #machine.vm.synced_folder ".", "/home/core/share", id: "core", :nfs => true, :mount_options => ['nolock,vers=3,udp']

      cloud_config_path = "/tmp/node.yaml"
      
      if i == 1
        cloud_config_path = "/tmp/master.yaml"
      end

      machine.vm.provision :file, :source => "#{cloud_config_path}", :destination => "/tmp/vagrantfile-user-data"
      machine.vm.provision :shell, :inline => "mv /tmp/vagrantfile-user-data /var/lib/coreos-vagrant/", :privileged => true
    end
  end  
end
