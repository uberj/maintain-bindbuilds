from hostlib2.utilities import long2ip
import pdb
import re
import printer
"""
A Zone object should be initialized at a base domain. From that domain it should start to
build a zone file. These are the steps it shuold take to build it's zone file.
1) If there is an SOA, print it.
2) Print an $ORIGIN directive
3) Print Name Servers
4) Print MX records
5) Print A records
6) Print CNAMES
7) Get all domains that are `children` of that domain.
    7.a) For each child.
        * If there is an SOA for that child, make a new Zone object.
          Initialize that new zone with the new domain. Call walk_domain.
        * If this the subdomain is part of this Zone (it has no new SOA),
          recurse.

PROBLEMS:
    MX records are being finiky. Example is kbvr.com.
        Notes kbvr: Search zone_mx for name= %skbvr%s
        It's domain is 543 which links to the com domain in the domain table.
    Solution: Add a record in the zone_mx table with name=''
"""
class Zone(object):
    BUILD_DIR="./build"
    SERIAL = 1

    """
    @cur: database cursor
    @zone_fd: file descriptor to the db.* file (.*in-addr.arpa files are generated inside later)
    @domain: a maintain 'id' int corresponding to dname
    @dname: the actual string representation of the domain
                This helps bootstrap the process of generating revrse pointer .*in-addr.arpa files.

    """
    def __init__( self, cur, zone_fd, domain, dname ):
        self.cur = cur
        self.domain = domain
        self.dname = dname
        self.printer = printer.Printer( fd=zone_fd )




    def walk_domain( self, cur_domain , dname ):
        #TODO Consider moving the SOA genration into __init__
        if self.check_for_SOA( cur_domain, dname ):
            self.gen_SOA( cur_domain, dname )
        self.gen_domain( cur_domain, dname )
        self.cur.execute("SELECT * FROM `domain` WHERE `master_domain`=%s;" % (cur_domain))
        domains = self.cur.fetchall()
        for subdomain in domains:
            child_name = subdomain[1]
            child_domain = subdomain[0]
            if self.check_for_SOA( child_domain, child_name ):
                zone_fd = open( "%s/%s" % (Zone.BUILD_DIR, child_name), "w+")
                new_zone = Zone( self.cur, zone_fd, child_domain, child_name )
                new_zone.walk_domain( child_domain, child_name )
                continue
            self.walk_domain( child_domain, child_name )

    def gen_domain( self, domain, dname ):
        print "Generating %s" % (dname)
        self.gen_ORIGIN( domain, dname, 999 )
        self.gen_NS( domain, dname )
        self.gen_MX( domain, dname )
        self.gen_A( domain, dname )
        self.gen_CNAME( domain, dname )
        if dname == 'oregonstate.edu':
            self.gen_dyn_ranges()

    def gen_MX( self, domain, dname ):
        self.cur.execute("SELECT * FROM `zone_mx` WHERE `domain`='%s' ORDER BY `name`;" % (domain))
        records = self.cur.fetchall()
        for record in records:
            if record[1] == "":
                name = "@"
            else:
                name = record[1]
            domain = record[2]
            ttl = record[5]
            server = record[3]
            prio = record[4]
            ttl = record[5]
            self.printer.print_MX( name, domain, ttl, prio, server  )
    """
    This function may be redundant.
    """
    def check_for_SOA( self, domain, dname ):
        self.cur.execute("SELECT * FROM `soa` WHERE `domain`='%s' ;" % (domain))
        records = self.cur.fetchall() # Could use fetch one. Want to do check though.
        if len(records) > 1:
            self.printer.print_raw( ";Sanity Check failed\n" )
        if not records:
            # We don't have an SOA for this domain.
            return False
        else:
            return True

    def gen_SOA( self, domain, dname ):
        self.cur.execute("SELECT * FROM `soa` WHERE `domain`='%s' ;" % (domain))
        records = self.cur.fetchall() # Could use fetch one. Want to do check though.
        if len(records) > 1:
            self.printer.print_raw( ";Sanity Check failed" )
        if not records:
            # We don't have an SOA for this domain.
            self.printer.print_raw( ";No soa for "+dname+"  "+str(domain) )
            return
        record = records[0]
        primary_master = record[2]
        contact = record[3]
        REFRESH = record[4]
        RETRY = record[5]
        EXPIRE = record[6]
        MINIMUM = record[7] #TODO What is minimum, using TTL
        self.printer.print_SOA( dname, primary_master, contact, Zone.SERIAL, REFRESH, RETRY, EXPIRE, MINIMUM )

    def gen_ORIGIN( self, domain, dname, ttl ):
        origin = "$ORIGIN  %s.\n" % (dname)
        origin += "$TTL     %s\n" % (ttl)
        self.printer.print_raw( origin )

    def gen_CNAME( self, domain, dname ):
        self.cur.execute("SELECT * FROM `zone_cname` WHERE `domain`='%s';" % (domain))
        records = self.cur.fetchall()
        for record in records:
            self.printer.print_CNAME( record[2], record[1] )

    def gen_dyn_ranges( self ):
        self.printer.print_raw( "; Gen dyn_ranges\n" )
        self.cur.execute("SELECT start, end FROM ranges WHERE type='dynamic' ORDER by start")
        ip_ranges = self.cur.fetchall()
        for ip_range in ip_ranges:
            for ip in range(ip_range[0],ip_range[1]+1):
                ip = long2ip(ip)
                self.printer.print_A( ip.replace('.','-'),ip )
    """
    domain: maintain id of the domain
    dname: the base name of that domain. i.e. domain 218 has dname oregonstate.edu
    """

    def gen_A( self, domain, dname ):
        self.gen_host( domain, dname )
        self.gen_forward_pointers( domain, dname )

    """
    Generate all A records from the pointer table (forward pointers)
    """
# This might generate duplicate records TODO since we are just filtering on dname
# If we did a tree search starting at the leaf nodes this would work better.
# Right now all subdomain of some domain also generate all forward pointers.
# Need a way to only print a forward pointer once.
# Solution?
# Before we do ORIGIN buisness print absolute domain names with their ip's
# We could also print a $ORIGIN ., and at the end print $ORIGIN domain.
    def gen_forward_pointers( self, domain, dname ):
        sql = "SELECT * FROM `pointer` WHERE hostname LIKE '%"+dname+"' AND `type`='forward' ORDER BY hostname"
        self.cur.execute(sql)
        records = self.cur.fetchall()
        # We have abosulte names in the pointer table so print a root origin.
        self.gen_ORIGIN( domain, '', 999 )
        for record in records:
            if record[1] == 0:
                continue
            self.printer.print_A( record[2] , long2ip(record[1]) )
        # Revert to dname origin.
        self.gen_ORIGIN( domain, dname , 999 )

    """
    Generate all A records from the host table.
    """
    def gen_host( self, domain, dname ):
        self.cur.execute("SELECT * FROM `host` WHERE `domain`='%s';" % (domain))
        records = self.cur.fetchall()
        for record in records:
            if record[1] == 0:
                continue
            self.printer.print_A( record[3] , long2ip(record[1]) )

    def gen_NS( self, domain, dname ):
        self.cur.execute("SELECT * FROM `nameserver` WHERE `domain`='%s';" % (domain))
        records = self.cur.fetchall()
        self.printer.print_NS( '', [ record[1] for record in records ] )
