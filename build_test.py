import unittest
import subprocess
import pdb
import pprint
import smtplib

class Tester(object):
    def __init__(self):
        self.mail = smtplib.SMTP('smtp.oregonstate.edu')
        self.email = "bind@ns-dev.nws.oregonstate.edu"
        self.email_to = "minions@net.oregonstate.edu"

    def build_test( self, zone, filepath ):
        def _test( self ):
            ret = subprocess.call(["named-checkzone","-q",str(zone), str(filepath)])
            self.assertEqual(ret, 0, "named-checkzone %s %s" % (zone, filepath))

        return _test

    class TestBindBuilds(unittest.TestCase):
        pass


    def run_zone_tests(self, tests):
        for zone, filepath in tests:
            func_name = "test_%s" % (zone.replace('.','_'))
            test = self.build_test( zone, filepath )
            setattr(self.TestBindBuilds, func_name, test)
        suite = unittest.TestLoader().loadTestsFromTestCase(self.TestBindBuilds)
        test_results = unittest.TextTestRunner(verbosity=2).run(suite)
        if test_results.errors or test_results.failures:
            # This could be more pretty
            result_email = "To: %s\n" % (self.email_to)
            result_email += "From: %s\n" % (self.email)
            result_email += "Subject: %s\n" % ("Bind build notifications")
            if test_results.errors: result_email += "Errors:\n"+pprint.saferepr(test_results.errors)
            if test_results.failures: result_email += "Failures:\n"+pprint.saferepr(test_results.failures)
            self.mail.sendmail(self.email, self.email_to, result_email)

if __name__ == "__main__":
    TESTS = [("orst.edu", "/var/named/orst.edu"),("oregonstate.edu", "/var/named/oregonstate.edu")]
    t = Tester()
    t.run_tests( TESTS )
