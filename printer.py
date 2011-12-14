import sys

"""
A class to print BIND records.
"""
class Printer(object):
    def __init__( self, fd=sys.stdout, AJUST1=30, AJUST2=10 ):
        self.fd = fd
        self.AJUST1 = AJUST1
        self.AJUST2 = AJUST2

    def print_raw( self, message ):
        self.fd.write( message )

    def print_rr( self, name, data , rr_type, terminal="" ):
        name = name.ljust(self.AJUST1," ")
        self.fd.write("%s %s%s%s%s\n" % (name,rr_type," "*self.AJUST2,data,terminal))

    def print_PTR( self, ip, dname ):
        self.print_rr( ip, dname, "PTR", "." )

    def print_A( self, dname, ip , terminal=""):
        self.print_rr( dname, ip, "A", terminal )

    def print_CNAME( self, dname, cname ):
        self.print_rr( dname, cname, "CNAME", "." )

    def print_MX( self, name, domain, ttl, prio, server ):
        self.print_rr( name, str(prio)+" ".rjust(3," ") , 'MX', server )

    def print_NS( self, dname, nameservers ):
        if not nameservers:
            return
        dname = dname.ljust(self.AJUST1," ")
        padding = "@".ljust(self.AJUST1," ")
        for ns in nameservers:
            self.fd.write("%s NS%s%s.\n" % (padding," "*self.AJUST2,ns))

    def print_SOA( self, dname, primary_master, contact,serial, refresh, retry, expire, minimum ):
        dname = dname+"."
        dname = dname.ljust(self.AJUST1," ")
        off = 9
        soa = ""
        soa += "%s IN SOA %s. %s. (\n" % (dname, primary_master, contact)
        soa +="\n"
        soa += str(serial).rjust(self.AJUST1+off," ")
        soa +="\n"
        soa += str(refresh).rjust(self.AJUST1+off," ")
        soa +="\n"
        soa += str(retry).rjust(self.AJUST1+off," ")
        soa +="\n"
        soa += str(expire).rjust(self.AJUST1+off," ")
        soa +="\n"
        soa += str(minimum).rjust(self.AJUST1+off," ")+" )"
        soa +="\n"
        self.fd.write(soa)

