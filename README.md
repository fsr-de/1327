1327
====

[![Build Status](https://travis-ci.org/fsr-de/1327.svg?branch=master)](https://travis-ci.org/fsr-de/1327)
[![Requirements Status](https://requires.io/github/fsr-de/1327/requirements.svg?branch=master)](https://requires.io/github/fsr-de/1327/requirements/?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/dbb7db2d1306434e92a947a9214671ba)](https://www.codacy.com/app/fsr-de/1327)
[![Coverage Status](https://coveralls.io/repos/github/fsr-de/1327/badge.svg?branch=master)](https://coveralls.io/github/fsr-de/1327?branch=master)

A student representatives website. This project is live! You can see a working instance of 1327 [here](https://myhpi.de/home)!

## Development

To be able to contribute to 1327, you need to get the source code with all dependencies. Please note, that submodules for *bootstrap*, *font-awesome* and *bootstrap-markdown* are in use:

```bash
git clone https://github.com/fsr-itse/1327.git
```

Freshly created code needs to be tested - besides our use of unit tests, linting and continous integration, it is possible to run the application in a non-production environment using *Vagrant* or a *Virtual Environment*.

### Vagrant

You can simply set up an execution environment using `vagrant`:

```bash
vagrant up
```

This will set up a virtual machine and run it. Running this for the first time might take a while.

To connect to it and start the application do:

```bash
vagrant ssh
# This will take one inside the virtual machine
./manage.py run
```

At that point you created a vagrant box, running a [PostgreSQL](https://www.postgresql.org/) database server, [Apache](https://httpd.apache.org/) web server and the [Django](https://www.djangoproject.com/) application. The contents are available on the default port `8000`, which allows you to access the website at `http://localhost:8000`.

To login with your local user instead of the default OpenID login, you have to visit `http://localhost:8000/login?local_login=1`

### Virtual Environment

Another way of executing this django application is the use of a virtual python environment. This way bypasses the needs for a virtual machine and simplifies the life with multiple python versions installed:

```bash
virtualenv -p /usr/bin/python3 env
source env/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser --username=admin
python manage.py run
```

After you're done with these steps, you'll need to install all static dependencies
via [Yarn](https://yarnpkg.com/lang/en/).
1. Install Yarn
2. go into the directory `static`
3. run the command `yarn`

## Deployment

For deploying on a single machine 1327 you'll need to install all requirements from `requirements-deploy.txt`, and you can follow these [instructions](https://github.com/fsr-itse/1327/wiki/Deployment), for setting up a webserver and starting all scripts using a Process Control System, if you like.
You'll also need to setup yarn, as indicated in the last section.

## License

The software is licensed under the terms of the [MIT license](LICENSE). Please note, that non-MIT-licensed contents might be part of this repository.
