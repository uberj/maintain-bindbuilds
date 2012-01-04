from fabric.api import *

master = 'ns-dev.nws.oregonstate.edu'
slaves = ['ns4jr.nws.oregonstate.edu']
env.hosts = slaves

maintain_dir = "/data/maintain"

def uname():
    run('uname -a')

def build():
    pass

def deploy_maintain_named_conf():
    local_conf = maintain_dir + "/staging/named.conf.maintain"
    for slave in slaves:
        local("scp "+local_conf+" "+slave+":/etc/bind/")

    local("cp "+local_conf+" /etc/bind/named.conf.maintain")
    if run("/etc/init.d/bind9 reload").failed:
        print "Slaved failed to reload"

def deploy_slave_delegated_conf():
    local_conf = "/etc/bind/named.conf.delegated"
    for slave in slaves:
        local("scp "+local_conf+" "+slave+":/etc/bind/")

    run("/etc/init.d/bind9 reload")


def deploy_slave_named_conf():
    local_conf = maintain_dir + "/staging/named.conf.maintain.slave"
    for slave in slaves:
        local("scp "+local_conf+" "+slave+":/etc/bind/")

    local("cp "+local_conf+" /etc/bind/named.conf.maintain.slave")
    if run("/etc/init.d/bind9 reload").failed:
        print "Slaved failed to reload"

def reload_bind():
    if local("/etc/init.d/bind9 reload").failed:
        print "oops"

def build_configs_into_staging():
    local("python main.py -c -d staging")

def setup():
    with settings(warn_only=True):
        if local("test -d build").failed:
            local("mkdir build")
        if local("test -d staging").failed:
            local("mkdir staging")

def changes_in_maintain_named_conf():
    local_conf = "named.conf.maintain"
    with settings(warn_only=True):
        if local("diff /etc/bind/"+local_conf+" "+maintain_dir+"/staging/"+local_conf+" > /dev/null").failed:
            return True
        else:
            return False


def changes_in_slave_named_conf():
    local_conf = "named.conf.maintain.slave"
    with settings(warn_only=True):
        if local("diff /etc/bind/"+local_conf+" "+maintain_dir+"/staging/"+local_conf+" > /dev/null").failed:
        #if local("diff /etc/bind/"+local_conf+" "+maintain_dir+"/staging/"+local_conf).failed:
            return True
        else:
            return False

def fix_perms():
    local("chown -R bind /etc/bind")

def deploy():
    cd( maintain_dir )
    setup()
    ### Build all
    local("pwd")
    local("python main.py -c --build_dir=/etc/bind/zones --bind_dir="+maintain_dir+"/staging")
    fix_perms()
    ### Build bind configs
    if changes_in_maintain_named_conf():
        deploy_maintain_named_conf()
    if changes_in_slave_named_conf():
        deploy_slave_named_conf()
    deploy_slave_delegated_conf()
    fix_perms()
    reload_bind()
