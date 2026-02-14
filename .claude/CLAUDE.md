# CLAUDE.md

## Principles of Action
- **Completely align with users:** For any ambiguity, we must break it down into smaller parts and conduct interviews using the AskUserQuestion Tool.
- **Minimal changes:** Only make changes that are directly requested. Do not refactor, add comments, or "improve" surrounding code unless asked.

## Project Overview
This is a Claude Code plugin marketplace repository. It contains custom plugins (`danishi`, `pdf-editor`), hooks, skills, agents, and shared settings.

### Structure
- `plugins/danishi/` - Personal base toolkit (slash commands, hooks, MCP servers)
- `plugins/pdf-editor/` - PDF manipulation toolkit (Python scripts, specialized agent)
- `.claude/settings.json` - Shared Claude Code settings
- `.claude-plugin/marketplace.json` - Plugin marketplace metadata
- `.github/workflows/` - GitHub Actions for Claude Code integration

## Quality Standards

### Testing
- Python scripts (`plugins/pdf-editor/scripts/`) must handle edge cases: empty PDFs, invalid page ranges, missing files.
- Test with actual PDF files before committing changes to scripts.
- Validate JSON files (`settings.json`, `plugin.json`, `marketplace.json`, `hooks.json`) with `jq` or a JSON linter before committing.

### Error Handling
- Python scripts must provide clear error messages with file paths and page numbers on failure.
- Exit with non-zero status codes on error — never silently succeed.
- Hook commands should fail gracefully if the platform does not support them (e.g., `osascript` on non-macOS).

### Configuration Quality
- IMPORTANT: All JSON config files must be valid. Run `python -m json.tool <file>` to verify.
- Plugin `plugin.json` files must include `name`, `version`, `author`, and `description`.
- Hooks must specify the correct event type (`Notification`, `Stop`, `PreToolUse`, etc.).

### Commit Messages
- Write in English.
- Use imperative mood: "Add feature" not "Added feature".
- Keep the first line under 72 characters.

## Build & Validate
- Validate JSON: `python -m json.tool .claude/settings.json`
- Test PDF scripts: `pip install pypdf && python plugins/pdf-editor/skills/pdf-editor/scripts/example.py`
- Lint markdown: use any available markdown linter

## Gotchas
- Hook commands use macOS-specific `osascript` and `afplay` — they will not work on Linux/Windows.
- The `pdf-editor` plugin requires the `pypdf` library (`pip install pypdf`).
- NEVER modify `marketplace.json` schema fields without updating all referenced plugin paths.
