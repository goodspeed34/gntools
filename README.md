# GNtools

## Build

## Localization

Create the latest po template file:

```
xgettext --keyword=translatable --sort-output -d GNtools -o locales/GNtools.pot res/*.glade *.py
```

Update or create the po file for your locale:

```
msgmerge --update locales/LANG/LC_MESSAGES/GNtools.po locales/GNtools.pot
```