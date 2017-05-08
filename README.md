PC-QA
=====

Usage
-----

```
$ cp qa/settings.py.sample qa/settings.py
$ pip install -r requirements.txt
$ pip install -r localqa/requirements.txt
$ mkdir data
$ curl https://github.com/yuantailing/pc-qa/releases/download/v0.0.1/series.tar.gz -L | tar xzf - -C data
$ python manage.py migrate
$ python manage.py runserver
```
