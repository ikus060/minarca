# Development

This section provide details for those who want to contributes to the development.

## Translation

Reference <http://babel.edgewall.org/wiki/Documentation/setup.html>

Minarca may be translated using `.po` files. This section describe briefly
how to translate Minarca. It's not a complete instruction set, it's merely a reminder.

Extract the strings to be translated:

    cd minarca-client
    python setup.py extract_messages

Create a new translation:

    cd minarca-client
    python setup.py init_catalog --local fr --input-file minarca_client/locales/messages.pot --output-dir minarca_client/locales

Update an existing translation:

    cd minarca-client
    python setup.py update_catalog --local fr

Compile catalog:

    python setup.py compile_catalog

## Code Signing

Reference <https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/>
