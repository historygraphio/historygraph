Readme
======

Readme for the historygraph library.

Installation
============

Set up a virtualenv for Python 2.7 and install the necessary stuff
```
virtualenv venv
source venv/bin/activate
pip install pip --upgrade
pip install urllib3[secure]
pip install -r requirements.txt
```

To run the unittests

```
python -B -m unittest discover
```

Set up a virtualenv for Python 3 and install the necessary stuff
```
virtualenv venv3 -p python3
source venv3/bin/activate
pip install pip --upgrade
pip install urllib3[secure]
pip install -r requirements.txt
```

To run the unittests

```
python -B -m unittest discover
```

Run all of the tests in tox

```
virtualenv venv
source venv/bin/activate
pip install pip --upgrade
pip install urllib3[secure]
pip install -r requirements.txt

tox --recreate
```

Run tests in Idle
=================

Sometimes tests fail in ways which in may be useful for us to run them in a debugger.
Luckily Idle is free. But it is a part of the standard Python library and a
100% pure python program it's.

If you are using Ubuntu it is not included in Ubuntu's version of the python
standard library.

Install with
```
sudo apt-get install idle idle3
```
This will get both the Python2 and Python3 versions

You can start up Idle by typing
```
python -m idlelib.idle
```
This works in both Python 2 and 3 (From this stack overflow answer [https://stackoverflow.com/a/38104835])

Run the following at the internal command line inside Idle. You will probably
want to enable debugging and set some break points

```
import unittest
import tests.test_textedit.test_textedit_replication_conflict
suite = unittest.TestLoader().loadTestsFromTestCase( tests.test_textedit.test_textedit_replication_conflict.TextEditTestReplication )
unittest.TextTestRunner(verbosity=2).run( suite )
```

(From this stack overflow answer [https://stackoverflow.com/a/3695937])
