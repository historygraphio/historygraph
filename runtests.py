# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

# From this stack overflow answer https://stackoverflow.com/a/3695937
import unittest
import tests.test_textedit.test_textedit_replication_conflict
# Change this line to the test suite you want to run
suite = unittest.TestLoader().loadTestsFromTestCase( tests.test_textedit.test_textedit_replication_conflict.TextEditTestReplication )
unittest.TextTestRunner(verbosity=2).run( suite )
