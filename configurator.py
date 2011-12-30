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
    def __init__( self, db_cur, filename="named.conf.maintain", bind_dir="/etc/bind", build_dir="/var/named" ):
        self.bind_dir = bind_dir # Where to put the named.conf file
        self.build_dir = build_dir # Where the zone files are kept
        self.cur = db_cur # Database cursor
        self.master_filename = filename
        self.slave_filename = filename+".slave"
        self.master_conf_fd = open(self.bind_dir + "/" + self.master_filename, "w+")
        self.slave_conf_fd = open(self.bind_dir + "/" + self.slave_filename, "w+")
        self.bind_tests = build_test.Tester()
        self.test_cases = [] # tests cases to be run later.
                             # The format for a test case should be ( 'test_name', [args to subprocess] )

    def build_named_conf_master( self ):
        print "Building "+self.master_filename+" in "+self.bind_dir
        for domain in self.get_auth_domains():
            self.master_conf_fd.write( self.gen_auth_zone( domain, self.build_dir+"/"+domain ) )
            self.test_cases.append( (domain.replace('.','_'), ["named-checkzone","-q",domain, self.build_dir+"/"+domain ]) )

    def build_named_conf_slave ( self ):
        print "Building slave "+self.slave_filename+" in " + self.bind_dir
        for domain in self.get_auth_domains():
            self.slave_conf_fd.write( self.gen_slave_zone ( domain, "128.193.15.15", self.build_dir + "/" + domain ) )

    def test_zone_files( self ):
        self.bind_tests.run_zone_tests( self.test_cases )


    def gen_auth_zone( self,  name, file_path ):
        l  = """zone "%s" {\n""" % (name)
        l += """    type master;\n"""
        l += """    file "%s";\n""" % (file_path)
        l += """};\n"""
        return l

    def gen_slave_zone ( self, name, masters, file_path ):
        l  = """zone "%s" {\n""" % (name)
        l += """    type slave;\n"""
        l += """    file "%s";\n""" % (file_path)
        l += """    masters {\n"""
        l += """        %s;\n""" % (masters)
        l += """    };\n"""
        l += """}\n"""
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
