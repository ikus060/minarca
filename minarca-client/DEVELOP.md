# Build Minarca Client

To build minarca client you need to install maven and icotool (used to create
.ico file from pngs). The following command should install them and there
dependencies.

    sudo apt-get install maven icoutils

Once the dependencies are installed, should may compile minarca as follow:

    mvn clean install

# Translation

minarca project uses gettext plugin to support translation using `.pot` and
`.po` files. You may update the translation or add a new translation as follow.

To extract translatable string and update the `.pot` file

    mvn gettext:gettext

To update the translation file `.po`

    mvn gettext:merge


# Code signing

Minarca build script may sign the code. To enabled signing, call maven with the
following options:
    
    mvn clean install -Dsign.certs.path=authenticode-certs.pem -Dsign.key.path=authenticode.pem -Dsign.passphrase=CHANGEME
    
To sign the code, you need to have `osslsigncode` installed locally.

    sudo apt-get install libssl-dev libcurl4-gnutls-dev autoconf
    wget http://nchc.dl.sourceforge.net/project/osslsigncode/osslsigncode/osslsigncode-1.7.1.tar.gz
    tar zxvf osslsigncode-1.7.1.tar.gz
    cd osslsigncode-1.7.1
    ./configure
    make
    sudo make install
    
Reference: https://development.adaptris.net/users/lchan/blog/2013/06/07/signing-windows-installers-on-linux/ 

# Advance configuration

* log.minarca.level = ERROR|WARN|INFO|DEBUG, default DEBUG
* log.root.level = ERROR|WARN|INFO|DEBUG, default WARN
* minarca.singleinstance.backup.port = <port>, default 52356
* minarca.singleinstance.backup.port = <port>, default 52356

   