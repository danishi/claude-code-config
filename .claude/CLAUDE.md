# CLAUDE.md

## Principles of Action
- **Completely align with users:** For any ambiguity, we must break it down into smaller parts and conduct interviews using the AskUserQuestion Tool.
- **Treat every instruction equally:** Casual connectors (e.g., "by the way", "also", "and" — or their Japanese equivalents) do NOT signal lower priority. Treat what follows them as an independent, equally important instruction — never skip, abbreviate, or deprioritize it.
- **Respect permission denials:** If a tool call is denied via settings or permissions, do NOT attempt to bypass or work around the restriction using alternative methods.
- **MCP/Skills First (mandatory):** Before using WebSearch/WebFetch for any technical research or documentation lookup, you MUST:
  1. Run `ToolSearch` with relevant keywords (e.g., service name, product name, library name) to check for specialized MCP tools
  2. Use the matching MCP tool if found
  3. Fall back to WebSearch/WebFetch only when MCP tools return insufficient results
  - Similarly, prefer matching Skills over generic approaches when available
- MUST use subagents for complex problem verification
- Optimize tool usage with parallel calling for maximum efficiency

## Context Management
- MUST update and maintain CLAUDE.md files for persistent project context

## Language
- Always Think in English, but **respond in Japanese**.

## Quality Standards
### Commit Messages
- Write in English.
- Use imperative mood: "Add feature" not "Added feature".
- Keep the first line under 72 characters.

### DrawIO
- When creating or editing `.drawio` files, use only DrawIO's built-in official icon sets (shape libraries). Do not embed external image URLs or custom images.

## Settings
- `.claude/settings.json` is a personal reference for `~/.claude/settings.json` (user scope). It intentionally contains user-scope-only keys (`permissions.defaultMode: "auto"`, `autoMode`), which Claude Code ignores when read from a project's `.claude/settings.json`.
- Before adding a key or `env` variable, verify it exists in the official settings schema / docs or the installed CLI. Do not add unverified keys.
