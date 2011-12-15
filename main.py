import database
from zone import Zone
from reverse_zone import Reverse_Zone
from configurator import Configurator

db = database.Database()
cur = db.get_cursor("maintain_sb")

build_dir = "../named"
fd = open(build_dir+"db.none", "w+")

# build named.conf.maintain file
cf = Configurator( db_cur = cur, named_dir=build_dir, build_dir="/vagrant/named")
cf.build_named_conf()
"""
# Regular zones
Zone.BUILD_DIR = build_dir
reg_zone = Zone( cur, fd, 0, "." )
reg_zone.walk_domain( 0, "." )
"""

# Reverse zones
Reverse_Zone.BUILD_DIR = build_dir
rev_zone = Reverse_Zone( cur, fd, 0, '' )
records = rev_zone.gen_all_records()
rev_zone.walk_tree( 0, 'root', records )
"""


# Test for records that were not added to the build.
for record in records:
    print "%s %s" % (long2ip(record[0]), record[1])
"""
