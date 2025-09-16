# Development

This section provides details for those who want to contribute to the development.

## Translation

Reference <http://babel.edgewall.org/wiki/Documentation/setup.html>

Minarca may be translated using `.po` files. This section describes briefly
how to translate Minarca. It's not a complete instruction set, it's merely a reminder.

Extract the strings to be translated:

    tox -e babel_extract

Create a new translation:

    tox -e babel_init -- --local fr

Update an existing translation:

    tox -e babel_update -- --local fr

Compile all existing translation:

    tox -e babel_compile

## Code Signing

Reference <https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/>

