# CLAUDE.md

## Principles of Action
- **Completely align with users:** For any ambiguity, we must break it down into smaller parts and conduct interviews using the AskUserQuestion Tool.
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
