import unittest
import tests.test_booleanregister
suite = unittest.TestLoader().loadTestsFromTestCase( tests.test_booleanregister.BooleanRegisterTestCase )
unittest.TextTestRunner(verbosity=2).run( suite )
