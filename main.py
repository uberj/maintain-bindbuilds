from zone import Zone
from reverse_zone import Reverse_Zone
import database

db = database.Database()
cur = db.get_cursor("maintain_sb")
fd = open("./build_test/db.none", "w+")

build_dir = "./build_test"

# Regular zones
Zone.BUILD_DIR = build_dir
reg_zone = Zone( cur, fd, 0, "." )
reg_zone.walk_domain( 0, "." )

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
