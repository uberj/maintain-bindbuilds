import build_test
"""
Helper class to build named.conf files.
"""
class Configurator(object):

    """
    @param bind_dir: Where bind is located. This where the the named.conf.maintain file will be put.
    @param build_dir: Where the actual zone files will be placed after the build completes (bind needs to know this).
    @test_file: a generated bashscript that tests all zone files generated for syntax errors.
    """
    def __init__( self, db_cur, bind_dir="/etc/bind", build_dir="/var/named", test_file="/tmp/maintain_checkzones" ):
        self.bind_dir = bind_dir # Where to put the named.conf file
        self.build_dir = build_dir # Where the zone files are kept
        self.cur = db_cur# Database cursor
        self.conf_fd = open(self.bind_dir+"/"+"named.conf.maintain", "w+")
        self.named_checkzone = open(test_file, "w+")
        self.named_checkzone.write("#!/bin/bash\n")
        self.bind_tests = build_test.Tester()

    def build_named_conf( self ):
        print "Building named.conf.maintain in "+self.bind_dir
        test_cases = [] # Build some tests cases to be run later.
        for domain in self.get_auth_domains():
            self.conf_fd.write( self.gen_auth_zone( domain, "master", self.build_dir+"/"+domain ) )
            test_cases.append( (domain, self.build_dir+"/"+domain) )
        self.bind_tests.run_zone_tests( test_cases )


    def gen_auth_zone( self,  name, server_type, file_path ):
        l  = """zone "%s" {\n""" % (name)
        l += """        type %s;\n""" % (server_type)
        l += """        file "%s";\n""" % (file_path)
        l += """};\n"""
        return l


    def get_auth_domains( self ):
        domains = []
        for domain in self.get_soa_domains():
            name = self.get_domain( domain )
            if name is not None:
                domains.append(name[0])
        return domains

    def get_soa_domains( self ):
        self.cur.execute("SELECT domain FROM soa WHERE 1=1;")
        return self.cur.fetchall()

    def get_domain( self, domain ):
        self.cur.execute("SELECT name FROM domain WHERE id = %s;" % (domain) )
        return self.cur.fetchone()
