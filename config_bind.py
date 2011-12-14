import database

db = database.Database()
cur = db.get_cursor("maintain_sb")

def build_bind_config():
    for domain in get_auth_domains():
        print gen_auth_zone( domain, "master", "/whatever/"+domain )


def gen_auth_zone( name, server_type, file_path ):
    l  = """zone "%s" {\n""" % (name)
    l += """        type %s;\n""" % (server_type)
    l += """        file "%s";\n""" % (file_path)
    l += """};"""
    return l


def get_auth_domains():
    domains = []
    for domain in get_soa_domains():
        name = get_domain( domain )
        if name is not None:
            domains.append(name[0])
    return domains

def get_soa_domains():
    cur.execute("SELECT domain FROM soa WHERE 1=1;")
    return cur.fetchall()

def get_domain( domain ):
    cur.execute("SELECT name FROM domain WHERE id = %s;" % (domain) )
    return cur.fetchone()

build_bind_config()
print gen_auth_zone("herp","master","/tmp")
