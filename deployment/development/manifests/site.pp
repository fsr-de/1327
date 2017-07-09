stage { 'pre':
    before => Stage['main'],
}

node default {
    # update apt
    class { 'apt':
        stage    => pre
    }

    # general packages
    package { ['git', 'build-essential', 'vim']:
        ensure => installed,
    } ->
    # python packages
    package { ['python3', 'python3-dev', 'python3-pip', 'gettext', 'libpq-dev']:
        ensure => installed,
    } ->
    package { ['nodejs', 'npm']:
        ensure => installed,
    } ->
    exec { "node-symlink":
        provider => shell,
        command => 'ln -s /usr/bin/nodejs /usr/bin/node'
    } ->
    exec { "install less":
        provider => shell,
        command => 'npm install -g less coffee-script'
    }


    class { 'postgresql::globals':
        python_package_name => 'python3'
    }

    class { 'postgresql::server':
    } -> postgresql::server::role { '1327':
        password_hash  => postgresql_password('1327', '1327'),
        createdb       => true
    } -> postgresql::server::db { '1327':
        owner          => '1327',
        user           => '1327',
        password       => ''
    } -> package { 'libapache2-mod-wsgi-py3':
        ensure         => latest,
    } -> exec { 'update-pip':
        provider       => shell,
        command        => 'sudo pip3 install -U pip',
        user        => 'vagrant'
    } -> exec { '/vagrant/requirements.txt':
        provider       => shell,
        command        => 'pip3 --log-file /tmp/pip.log install --user -r /vagrant/requirements.txt',
        user        => 'vagrant'
    } -> exec { '/vagrant/requirements-test.txt':
        provider       => shell,
        command        => 'pip3 --log-file /tmp/pip.log install --user -r /vagrant/requirements-test.txt',
        user        => 'vagrant'
    } -> exec { 'install-psycopg2':
        provider    => shell,
        command     => 'pip3 --log-file /tmp/pip.log install --user psycopg2==2.7.1',
        user        => 'vagrant'
    } -> class { 'd1327':
        db_connector   => 'postgresql_psycopg2'
    }

    # apache environment
    class { 'apache':
        default_vhost   => false,
        user            => 'vagrant',
        group           => 'vagrant',
    }
    class { 'apache::mod::wsgi':
        wsgi_python_path            => '/vagrant'
    } -> apache::vhost { '1327':
        default_vhost               => true,
        vhost_name                  => '*',
        port                        => '80',
        docroot                     => '/vagrant/_1327/staticfiles',
        aliases                     => [ { alias => '/static', path => '/vagrant/_1327/staticfiles' } ],
        wsgi_daemon_process         => 'wsgi',
        wsgi_daemon_process_options => {
            processes => '2',
            threads => '15',
            display-name => '%{GROUP}',
            user => 'vagrant'
        },
        wsgi_process_group          => 'wsgi',
        wsgi_script_aliases         => { '/' => '/vagrant/_1327/wsgi.py' },
    }

    exec { 'auto_cd_vagrant':
        provider    => shell,
        command     => 'echo "\ncd /vagrant" >> /home/vagrant/.bashrc'
    }

    exec { 'alias_python_python3':
        provider    => shell,
        # the sudo thing makes "sudo python foo" work
        command     => 'echo "\nalias python=python3\nalias sudo=\'sudo \'" >> /home/vagrant/.bashrc'
    }
}
