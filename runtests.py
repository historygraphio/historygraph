import unittest
import tests.test_delete_documents
suite = unittest.TestLoader().loadTestsFromTestCase( tests.test_delete_documents.TestDeletion )
unittest.TextTestRunner(verbosity=2).run( suite )
