# claude-code-config
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/danishi/claude-code-config)

Personal repository for managing Claude Code settings, plugins, and development customizations.

## Features

This repository provides two custom plugins for Claude Code:

### danishi Plugin
Personal base toolkit with the following features:
- **Slash Command**: `/review-spec-doc` - Reviews system specification documents and outputs improvement suggestions in Markdown format
- **Hooks**: macOS notification integration (alerts when Claude requests permission and when tasks complete)
- **MCP Servers**: Pre-configured integration with context7, chrome-devtools, and aws-knowledge

### pdf-editor Plugin
PDF page manipulation toolkit supporting:
- Deleting pages
- Reordering pages
- Inserting pages from other PDFs
- Rotating pages (90/180/270 degrees)
- Splitting PDFs into multiple files
- Merging multiple PDFs into one

**Specialized Agent**: `pdf-operator` - Dedicated agent for efficient PDF operations with automatic script selection and execution

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

List available plugins:
```bash
claude plugin list
```

Install a specific plugin:
```bash
claude plugin install danishi
claude plugin install pdf-editor
```

## Usage

### pdf-editor Plugin

**Using the Specialized Agent:**
```bash
# Start the pdf-operator agent interactively
claude agent start pdf-operator

# Or run a one-off PDF operation
claude agent run pdf-operator "Delete pages 2-4 from document.pdf and save as output.pdf"
```

**Direct Skill Usage:**
You can also use Claude Code's natural language interface to perform PDF operations:
```
"Delete pages 2-4 from document.pdf"
"Rotate all pages in file.pdf by 90 degrees"
"Merge file1.pdf and file2.pdf into combined.pdf"
"Split document.pdf into individual pages"
```

**Requirements for pdf-editor:**
```bash
pip install pypdf
```

### danishi Plugin

**Document Review Command:**
```bash
/review-spec-doc <input-file-path> <output-file-path|auto>
```

Example:
```bash
/review-spec-doc ./docs/specification.md auto
```

### License

This is a personal configuration repository. Feel free to reference or fork for your own use.