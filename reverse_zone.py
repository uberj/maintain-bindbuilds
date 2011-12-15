import database
from utilities import ip2long, long2ip
import pdb
import pprint
import printer
import re
import copy

class Reverse_Zone(object):
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
        self.cur.execute("SELECT id, name FROM domain WHERE name LIKE '%.in-addr.arpa' AND master_domain="+str(cur_domain)+" ORDER BY name")
        domains = self.cur.fetchall()
        for domain in domains:
            child_domain = domain[0]
            child_dname = domain[1]
            if self.check_for_SOA( child_domain, child_dname ):
                rzone_fd = open( "%s/%s" % (Reverse_Zone.BUILD_DIR, child_dname), "w+")
                new_rzone = Reverse_Zone( self.cur, rzone_fd, child_domain, child_dname )
                new_rzone.gen_SOA( child_domain, child_dname ) # SOA ALWAYS has to be first thing.
                new_rzone.walk_tree( child_domain, child_dname, records )
            else:
                self.walk_tree( child_domain, child_dname, records )
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
        self.printer.print_SOA( dname, primary_master, contact, Reverse_Zone.SERIAL, REFRESH, RETRY, EXPIRE, MINIMUM )

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


    def build_tree( self, cur_domain, tree ):
        self.cur.execute("SELECT id FROM domain WHERE name LIKE '%.in-addr.arpa' AND master_domain="+str(cur_domain))
        domains = self.cur.fetchall()
        for domain in domains:
            parent_domain = domain[0]
            parent_tree = {}
            tree[parent_domain] = self.build_tree( parent_domain, parent_tree )
        return tree

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

"""
print rz.ip_from_domainname( '139.201.199.in-addr.arpa' )
print rz.ip_from_domainname( '10.in-addr.arpa' )
print rz.ip_from_domainname( '193.128.in-addr.arpa' )
print rz.ip_from_domainname( '16.211.140.in-addr.arpa' )
pp.pprint( gen_all_records() )
#pp.pprint( rz.build_tree(0, {}) )
#rz.walk_tree( rz.build_tree(0, {}), rz.gen_all_records() )
records = rz.gen_all_records()
before = len(records)
rz.walk_tree( 0, 'root', records )
print "id="+str(id(records))
after = len(records)
for record in records:
    print "%s %s" % (long2ip(record[0]), record[1])
#walk_tree( build_tree(0, '', {}), [])
print before
print after
"""
