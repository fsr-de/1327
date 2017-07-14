class d1327 ($db_connector) {
    $secret_key = random_password(30)
    file { '1327-localsettings':
        name    => '/vagrant/_1327/localsettings.py',
        content  => template('d1327/localsettings.py.erb')
    } -> exec { 'django-migrate':
        provider    => shell,
        command     => 'python3 manage.py migrate --noinput',
        user        => 'vagrant',
        cwd         => '/vagrant'
    } -> exec { 'django-collectstatic':
        provider    => shell,
        command     => 'python3 manage.py collectstatic --noinput',
        user        => 'vagrant',
        cwd         => '/vagrant'
    } -> exec { 'django-compilemessages':
        provider    => shell,
        command     => 'python3 manage.py compilemessages',
        user        => 'vagrant',
        cwd         => '/vagrant'
    }
}
