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
virtualenv venv -p python3
source venv/bin/activate
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

tox
```
