class cruft {
    Exec { path => "/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin" }
    package { 'htop':
        ensure => "present",
    }
    package { 'vim':
        ensure => "present",
    }
    package { 'tcpdump':
        ensure => "present",
    }
    package { 'vim-puppet':
        ensure => "present",
    }
    group { "puppet": # Lawl hack.
        ensure => "present",
    }

    exec { 'install vim-puppet':
        require => [Package['vim-puppet'],Package['vim']],
        command => "/usr/bin/vim-addons install puppet",
    }

    package { 'bind9':
        ensure => "present",
    }
    package { 'dnsutils':
        ensure => "present",
    }

    package { 'python-mysqldb':
        ensure => "present",
    }
    #### Maintain stuff (write module, soon).
    package { 'libdbi-perl':
        ensure => "present",
    }
    package { 'sql-client-5.1':
        ensure => "present",
    }
    package { 'mysql-common':
        ensure => "present",
    }
    #####
}
stage { 'pre': before => Stage['main'] }

node ns-dev {
    class { "cruft": stage => 'pre' }
    file {'/var/named':
        ensure => directory,
    }
}
