import database
import MySQLdb

try:
    con = MySQLdb.connect(
        host="db.nws.oregonstate.edu",
        user="root",
        passwd="ervillynal",
        )
    cur = con.cursor()
except:
    pass
sql_insert_template = "INSERT INTO maintain_sb.%s SELECT * FROM maintain.%s WHERE 1=1;"
sql_delete_template = "DELETE FROM maintain_sb.%s WHERE 1=1;"

tables = (  "domain",
            "host",
            "nameserver",
            "pointer",
            "ranges",
            "soa",
            "zone_cname",
            "zone_domain",
            "zone_mx" )


for table in tables:
    cur.execute( sql_delete_template % (table) )
    print sql_delete_template % (table)
    cur.execute( sql_insert_template % (table, table) )
    print sql_insert_template % (table, table)
