# Build Minarca

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


