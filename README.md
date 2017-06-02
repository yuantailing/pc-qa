PC-QA
=====

Usage
-----

```
$ git submodule update --init --recursive
$ pip install -r requirements.txt
$ pip install -r localqa/requirements
$ cp qa/settings.py.sample qa/settings.py
$ mkdir data
$ curl https://github.com/yuantailing/pc-qa/releases/download/v0.0.2/series.tar.bz2 -L | tar xjf - -C data
$ python manage.py migrate
$ python manage.py runserver
```
