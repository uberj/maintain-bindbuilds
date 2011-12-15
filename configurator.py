"""
Helper class to build named.conf files.
"""
class Configurator(object):

    def __init__( self, db_cur, named_dir="/etc/bind", build_dir="/var/named" ):
        self.named_dir = named_dir # Where to put the named.conf file
        self.build_dir = build_dir # Where the zone files are kept
        self.cur = db_cur# Database cursor
        self.conf_fd = open(self.named_dir+"/"+"named.conf.maintain", "w+")

    def build_named_conf( self ):
        for domain in self.get_auth_domains():
            self.conf_fd.write( self.gen_auth_zone( domain, "master", self.build_dir+"/"+domain ) )


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
