import unittest
import tests.test_textedit.test_textedit_replication_conflict
suite = unittest.TestLoader().loadTestsFromTestCase( tests.test_textedit.test_textedit_replication_conflict.TextEditTestReplication )
unittest.TextTestRunner(verbosity=2).run( suite )
