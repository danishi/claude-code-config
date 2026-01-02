# claude-code-config
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/danishi/claude-code-config)

Personal repository for managing Claude Code settings, plugins, and development customizations.

## Installation
### Adding the Marketplace

Add to your Claude Code settings file (`~/.config/claude/settings.json`):

```json
{
  "plugin_marketplaces": [
    "https://github.com/danishi/claude-code-config"
  ]
}
```

Or add directly via Claude Code command:

```bash
claude marketplace add https://github.com/danishi/claude-code-config
```

### Installing Plugins

```bash
claude plugin install [plugin]
```

ex: Installing PDF Editor plugin.

```bash
claude plugin install pdf-editor
```
