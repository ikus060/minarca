# Installation

Procedure to install minarca-plugins

    wget --user 'ikus060' --ask-password http://www.patrikdufresne.com/archive/minarca-plugins/minarca-plugins-0.9.1.dev1.tar.gz
    tar -zxvf minarca-plugins*.tar.gz
    cd minarca-plugins*
    sudo python setup.py install
    
Put in place the configuration file.

    sudo cp rdw.conf /etc/rdiffweb/
    
Restart rdiffweb

    sudo /etc/init.d/rdiffweb restart