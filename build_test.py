import unittest
import ConfigParser
import subprocess
import pdb
import pprint
import smtplib

class Tester(object):
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read("build.cfg")
        self.mail = smtplib.SMTP(self.config.get('Email', 'smtp_server'))
        self.local_email = self.config.get('Email', 'local_email')
        self.testing_email = self.config.get('Email', 'testing_email')

    def build_test( self, args):
        def _test( self ):
            ret = subprocess.call(args)
            self.assertEqual( ret, 0, args )

        return _test

    class TestBindBuilds(unittest.TestCase):
        pass


    def run_zone_tests(self, tests):
        for test in tests:
            lambda_test = self.build_test( test[1] )
            setattr(self.TestBindBuilds, "test_"+str(test[0]), lambda_test )
        suite = unittest.TestLoader().loadTestsFromTestCase(self.TestBindBuilds)
        test_results = unittest.TextTestRunner(verbosity=2).run(suite)
        if test_results.errors or test_results.failures:
            # This could be more pretty
            email_to = self.testing_email
            result_email = "To: %s\n" % (email_to)
            result_email += "From: %s\n" % (self.local_email)
            result_email += "Subject: %s\n" % ("Bind build notifications")
            if test_results.errors: result_email += "Errors:\n"+pprint.saferepr(test_results.errors)
            if test_results.failures: result_email += "Failures:\n"+pprint.saferepr(test_results.failures)
            self.mail.sendmail(self.local_email, email_to, result_email)
