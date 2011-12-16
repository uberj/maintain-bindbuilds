import database
from utilities import ip2long, long2ip
import pdb
import pprint
import printer
import re
import copy

from env import *
from maintain2.domain.models import Domain
from maintain2.soa.models import Soa

class Reverse_Zone_Builder(object):
    BUILD_DIR="./build"
    SERIAL = 1


    def __init__( self, cur, zone_fd, domain, dname ):
        self.cur = cur
        self.domain = domain
        self.dname = dname
        self.printer = printer.Printer( fd=zone_fd )

    """
    Strategy:
    1) Build a tree of master and parent domains (masters are at the root).
    2) Get all ip's needed into a list.
    3) Do a right ordered traversal of the tree.
        * For all the ip's, if an ip belongs in that domain add it and remove it from the list.


    Walk through (right order traversal) the tree. SOA's should be generated and records should be removed from the record list.
    1) Call walk_tree on all children
    2) Determine if there is an SOA
        * print SOA if you have one
    3) Print NS asscoiated with domain
    4) Print all ip's in domain. Remove those ip's
    @param node: dictionary representing a tree
    @param records: global record list (global to recursive stack)
    """
    def walk_tree( self, cur_domain, cur_dname, records ):
        domains = Domain.objects.all()
        domains = domains.filter( master_domain = cur_domain, name__endswith = ".in-addr.arpa" ).order_by( "name" )
        for domain in domains:
            if self.check_for_SOA( domain.id, domain.name ):
                rzone_fd = open( "%s/%s" % (Reverse_Zone_Builder.BUILD_DIR, domain.name), "w+")
                new_rzone = Reverse_Zone_Builder( self.cur, rzone_fd, domain.id, domain.name )
                new_rzone.gen_SOA( domain.id, domain.name ) # SOA ALWAYS has to be first thing.
                new_rzone.walk_tree( domain.id, domain.name, records )
            else:
                self.walk_tree( domain.id, domain.name, records )
        self.gen_domain( cur_domain, cur_dname, records )

    """
    SQL Wrapper
    """
    def get_dname( self, domain ):
        cur.execute("SELECT name FROM domain WHERE id=%s" % (domain) )
        return cur.fetchone()[0]

    """
    Go go through all the records and add them to the correct zone file.
    1) If there is an SOA create a new Zone and call walk_tree.
    """
    def gen_domain( self, domain, dname, records ):
        if domain == 0 or dname == "root":
            print "Root domain, skipping"
            return
        else:
            print "Generating %s" % (dname)
        #if not re.search( "^10" ,self.ip_from_domainname(dname) ):
        #    return

        self.gen_ORIGIN( domain, dname, 999 )
        self.gen_NS( domain, dname )
        self.gen_ORIGIN( domain, 'in-addr.arpa', 999 )
        records_to_remove = []
        for record in records:
            longip, name = record
            ip = long2ip(longip)
            # TODO compile this
            search_string = "^"+self.ip_from_domainname(dname).replace('.','\.')
            if re.search( search_string, ip ):
                self.printer.print_PTR( ip, name )
                records_to_remove.append( record )

        for record in records_to_remove:
            records.remove(record)

        self.gen_ORIGIN( domain, dname, 999 )

    def gen_ORIGIN( self, domain, dname, ttl ):
        origin = "$ORIGIN  %s.\n" % (dname)
        origin += "$TTL     %s\n" % (ttl)
        self.printer.print_raw( origin )

    def gen_NS( self, domain, dname ):
        self.cur.execute("SELECT * FROM `nameserver` WHERE `domain`='%s';" % (domain))
        records = self.cur.fetchall()
        self.printer.print_NS( '', [ record[1] for record in records ] )

    """
    This function may be redundant.
    """
    def check_for_SOA( self, domain, dname ):
        soa = Soa.objects.filter( domain=domain )
        if len( soa ) > 1:
            self.printer.print_raw( ";Sanity Check failed\n" )
        if not soa:
            # We don't have an SOA for this domain.
            return False
        else:
            return True

    def gen_SOA( self, domain, dname ):
        soa = Soa.objects.filter( domain=domain )
        if len( soa ) > 1:
            self.printer.print_raw( ";Sanity Check failed" )
        if not soa:
            # We don't have an SOA for this domain.
            self.printer.print_raw( ";No soa for "+dname+"  "+str(domain) )
            return
        soa = soa[0] # We have this as a list so we can do some sanity checking on it.
        self.printer.print_SOA( dname, soa.primary_master, soa.hostmaster, \
                                Reverse_Zone_Builder.SERIAL, soa.refresh, soa.retry, \
                                soa.expire, soa.ttl )

    """
    We need ip's from: host, ranges, and pointer.
    """
    def gen_all_records( self ):
        # SQL is not like magic.
        PTR_records = []
        PTR_records +=  self.gen_host_records()
        PTR_records +=  self.gen_dyn_records()
        PTR_records +=  self.gen_pointer_records()
        return PTR_records

    def gen_pointer_records( self ):
        self.cur.execute("SELECT ip, hostname FROM pointer WHERE type = 'reverse';")
        return list(self.cur.fetchall())


    def gen_host_records( self ):
        self.cur.execute("SELECT host.ip, CONCAT(host.name, '.', domain.name) FROM host, domain WHERE host.ip != 0 AND host.domain = domain.id;")
        return list(self.cur.fetchall())

    def gen_dyn_records( self ):
        self.cur.execute("SELECT start, end FROM ranges WHERE type='dynamic' ORDER by start")
        ip_ranges = self.cur.fetchall()
        PTR_records = []
        for ip_range in ip_ranges:
            for ip in range(ip_range[0],ip_range[1]+1):
                PTR_records.append( (ip,long2ip(ip).replace('.','-')) )
        return PTR_records


    def ip_from_domainname( self, dname ):
        ip_data = re.search("(\d+).(\d*).?(\d*).?(\d*).*",dname)
        try:
            octets = list(reversed(list(ip_data.groups(0)))) # reverse the list, remove all duplicates (set), make it a list again.
        except NoneType:
            pdb.set_trace()
        while '' in octets:
            octets.remove('')
        #ip_mask = ( octets + (["0"] * 4) )[:4]
        return '.'.join(octets)
