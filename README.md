1327
====

[![Build Status](https://travis-ci.org/fsr-itse/1327.svg?branch=master)](https://travis-ci.org/fsr-itse/1327)
[![Code Health](https://landscape.io/github/fsr-itse/1327/master/landscape.svg?style=flat)](https://landscape.io/github/fsr-itse/1327/master)

A student representatives website. This is currently **work in progress** - please wait for basic functionality until the [launch](https://github.com/fsr-itse/1327/milestone/1) happened.

## Development

To be able to contribute to 1327, one needs to get the source code with all dependencies. Please note, that submodules for *bootstrap*, *font-awesome*, *bootstrap-markdown* and various *puppet* modules are in use:

```bash
git clone https://github.com/fsr-itse/1327.git
cd 1327
git submodule update --init
```

Freshly created code needs to be tested - besides our use of unit tests, linting and continous integration, it is possible to run the application in a non-production environment using *Vagrant* or a *Virtual Environment*.

### Vagrant

One can simply set up an execution environment using `vagrant`:

```bash
vagrant up --provision
```

At that point, one created a vagrant box, running a [PostgreSQL](https://www.postgresql.org/) database server, [Apache](https://httpd.apache.org/) web server and the [Django](https://www.djangoproject.com/) application. The contents are available on the default port `8000`, which allows one to access the website at `http://localhost:8000`. To create a new superuser for the application, execute `vagrant ssh` in the project directory and trigger the django user management system:

```bash
./manage.py createsuperuser --username=root
```

### Virtual Environment

Another way of executing this django application is the use of a virtual python environment. This way bypasses the needs for a virtual machine and simplifies the life with multiple python versions installed:

```bash
virtualenv -p /usr/bin/python3 env
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
python manage.py migrate
python manage.py createsuperuser --username=root
python manage.py runserver 0.0.0.0:8000
```

## License

The software is licensed under the terms of the [MIT license](LICENSE). Please note, that non-MIT-licensed contents might be part of this repository.
