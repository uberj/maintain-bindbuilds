import database
from zone_builder import Zone_Builder
from reverse_zone_builder import Reverse_Zone_Builder
from configurator import Configurator
from optparse import OptionParser
from utilities import ip2long, long2ip
# Import django env for models
from env import *


class Maintain(object):
    def __init__( self, build_zone, build_rev, build_config, bind_dir, build_dir, run_records_test = False ):
        db = database.Database()
        self.cur = db.get_cursor("maintain_sb")
        self.fd = open(build_dir+"/"+"db.none", "w+") # Zone needs this for bootstraping

        ### Behavior switches
        self.build_zone = build_zone # build forward zone files?
        self.build_rev = build_rev # build reverse zone files?
        self.build_config = build_config # build config file?
        ###

        ### Build dir's
        self.bind_dir = bind_dir
        self.build_dir = build_dir
        ###

        self.run_records_test = run_records_test

    def run( self ):
        if self.build_zone:
            self.zones_build( self.build_dir )
        if self.build_rev:
            self.reverse_zones_build( self.build_dir )
        if self.build_config:
            self.config_build( self.bind_dir , self.build_dir )

    # build named.conf.maintain file
    def config_build( self, bind_dir, build_dir ):
        cf = Configurator( db_cur = self.cur, bind_dir=bind_dir, build_dir=build_dir)
        cf.build_named_conf()

    def zones_build( self, build_dir ):
        # Regular zones
        Zone_Builder.BUILD_DIR = build_dir
        reg_zone = Zone_Builder( self.cur, self.fd, 0, "." )
        reg_zone.walk_domain( 0, "." )

    def reverse_zones_build( self, build_dir ):
        # Reverse zones
        Reverse_Zone_Builder.BUILD_DIR = build_dir
        rev_zone = Reverse_Zone_Builder( self.cur, self.fd, 0, '' )
        records = rev_zone.gen_all_records()
        rev_zone.walk_tree( 0, 'root', records )
        if self.run_records_test:
            print "===========THESE WERE NOT INCLUDED IN THE REVERSE BUILD==========="
            # Test for records that were not added to the build.
            for record in records:
                print "%s %s" % (long2ip(record[0]), record[1])

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-a", "--all", default=False, action="store_true", dest="build_all", help="Build everything")
    parser.add_option("-z", "--zone", default=False, action="store_true", dest="build_zone", help="Build forward zones")
    parser.add_option("-r", "--rev_zone", default=False, action="store_true", dest="build_rev", help="Build reverse zones")
    parser.add_option("-c", "--config", default=False, action="store_true", dest="build_config", help="Build named.conf.maintain file")
    parser.add_option("-t", "--run_records_test", default=False, action="store_true", dest="run_records_test", help="Run records test claus")
    parser.add_option("-b", "--build_dir", default="/var/named/", dest="build_dir", help="A directory to store the build output")
    parser.add_option("-d", "--bind_dir", default="/etc/bind", dest="bind_dir", help="Where to place the named.conf.maintain file")
    (options, args) = parser.parse_args()
    if options.build_all:
        print "***Building everything***"
        print "Building forward zones"
        print "Building reverse zones"
        print "Building named.conf.maintain into "+options.bind_dir
        print "Build dir is "+options.build_dir
        m = Maintain( True, True, True, options.bind_dir, options.build_dir, options.run_records_test )
    else:
        if options.build_zone : print "Building forward zones"
        if options.build_rev : print "Building reverse zones"
        if options.bind_dir and options.build_config : print "Building named.conf.maintain into "+options.bind_dir
        if options.build_dir : print "Build dir is "+options.build_dir
        m = Maintain( options.build_zone, options.build_rev, options.build_config, options.bind_dir, options.build_dir, options.run_records_test )
    m.run()


