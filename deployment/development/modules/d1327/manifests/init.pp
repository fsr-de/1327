class d1327 ($db_connector) {
    $secret_key = random_password(30)
    file { '1327-localsettings':
        name    => '/vagrant/_1327/localsettings.py',
        content  => template('d1327/localsettings.py.erb')
    } -> exec { 'django-migrate':
        provider    => shell,
        command     => 'python3 manage.py migrate --noinput',
        cwd         => '/vagrant'
    } -> exec { 'django-collectstatic':
        provider    => shell,
        command     => 'python3 manage.py collectstatic --noinput',
        cwd         => '/vagrant'
    } -> exec { '1327-flush-db':
        provider    => shell,
        command     => 'python3 manage.py flush --noinput',
        cwd         => '/vagrant'
    }
}
