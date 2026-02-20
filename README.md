# jeedom-i18n-tools

Reusable GitHub workflow for:

- Generating + translating Jeedom i18n JSON (via Mips2648/plugins-translations)
- Syncing and translating docs/fr_FR to other languages via DeepL

## Usage in a plugin

Create `.github/workflows/translate.yml`:

```yaml
name: Full translate

on:
  push:
    branches: [ beta ]
  workflow_dispatch:

jobs:
  translate:
    uses: Zyg0m4t1k/jeedom-i18n-tools/.github/workflows/full-translate.yml@main
    with:
      source_lang: fr_FR
      target_languages: "en_US,de_DE,es_ES"
    secrets:
      DEEPL_API_KEY: ${{ secrets.DEEPL_API_KEY }}
```

Add `DEEPL_API_KEY` as a repository secret.


## Manual edits protection

Docs files translated by the bot include an `AUTO_TRANSLATED` marker with hashes. If you edit a translated file manually, the bot will never overwrite it.
