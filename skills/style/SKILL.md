---
name: style
description: Pick, switch, clear, or create a Claude Code output style. Use when the user invokes /lej-output-fixer:style, asks to change how Claude writes (tone, verbosity, readability, formatting), or mentions output styles.
---

# Output Style Picker

You are helping the user choose or create an output style. Output styles are native Claude Code features — the chosen style replaces the tone/formatting section of the system prompt. Your job: show a menu, apply the choice, confirm.

## Step 1 — Gather the options

Use Claude Code's resolved catalog rather than maintaining a second list of style names. Check `claude --version` first. On v2.1.269 or newer, run this read-only local command from the current project directory:

```bash
claude --print --no-session-persistence --output-format json --plugin-dir "${CLAUDE_PLUGIN_ROOT}" /output-style
```

Read the JSON `result`: it lists the available built-in, plugin, user and project styles, their descriptions, and the current style. Keep each exact reference with its menu entry, including any plugin namespace. The catalog resolves names and precedence for this Claude Code version. Treat its `default` entry as **No output style**. Listing styles makes no model request; do not replace the command with a natural-language prompt.

On older versions, gather the catalog from files: read this plugin's `output-styles/*.md` under `${CLAUDE_PLUGIN_ROOT}` and its name from `.claude-plugin/plugin.json`; add the older built-ins Explanatory and Learning; then read user `~/.claude/output-styles/` and project `.claude/output-styles/` files, including project directories between the working directory and repository root. Use frontmatter `name` and `description` when present; otherwise use the filename without `.md` as the name. Files without frontmatter are valid styles. For bundled entries, form `<plugin-name>:<style-name>` references; user and built-in entries use plain names.

Check for an `outputStyle` field in, in order of precedence: `.claude/settings.local.json`, `.claude/settings.json`, `~/.claude/settings.json`. Note which file sets it. The catalog can echo a configured reference that no longer exists: if that reference is absent from the available entries, explain that it is unavailable rather than marking it active.

## Step 2 — Present the menu

Use the AskUserQuestion tool — never make the user type a style name freehand.

- Mark the currently active style in its option description.
- AskUserQuestion allows max 4 options per question. With more choices than fit, lead with the most relevant (bundled presets first, then the user's own) and make the last option "More options…" — if chosen, ask a follow-up question with the rest.
- The menu must always offer a path to two special entries:
  - **No output style** — return to Claude Code's default voice.
  - **Create new preset** — build a custom style (Step 4).

## Step 3 — Apply the choice

- **A style was chosen**: write `"outputStyle": "<reference>"` into `~/.claude/settings.json` (applies everywhere). If the user says they want it only for this project, use `.claude/settings.local.json` instead. Edit JSON carefully — preserve all existing keys. Use `jq` or a small `python3` round-trip, never a blind overwrite.
- **The reference format matters.** Write the exact reference attached to the selected catalog entry in Step 1. Plugin styles need their namespace prefix (for example, `lej-output-fixer:Scannable`); bare plugin style names silently do nothing. Built-in and user-created styles use plain names. Do not reconstruct the reference from an abbreviated menu label.
- **Precedence check**: if a more-specific settings file already sets `outputStyle` (local overrides project overrides user), tell the user their choice won't take effect until that override is removed, and offer to remove it.
- **No output style**: remove the `outputStyle` key from whichever settings file(s) set it. Confirm with the user before touching a project-level file they may share with a team.
- **Confirm**: state what's now active and which file controls it. Note that if the change doesn't take effect immediately, starting a new session will pick it up.

## Step 4 — Create new preset

Interview the user conversationally — a few quick questions, not a form:

1. What should it be called?
2. What's the one-line job? ("answers I can scan", "explain like I'm new", "just be brief")
3. Tone and verbosity — formal or casual? Terse or thorough?
4. Formatting rules — bullets vs. prose, headers, code-comment style, anything they always want?
5. Pet peeves — phrases or habits Claude should never do?

Save the agreed answers with [scripts/create_preset.py](scripts/create_preset.py), using Python 3 and a JSON object on stdin. Serialize the answers as JSON; keep user text out of shell arguments. For example:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/style/scripts/create_preset.py" <<'JSON'
{"name":"Their Name","description":"One line, shown in pickers","instructions":"- Max 3 sentences per paragraph.\n- Define unfamiliar terms."}
JSON
```

The helper quotes metadata, keeps coding instructions by default, and creates a new file in the user's `~/.claude/output-styles/` (or `CLAUDE_CONFIG_DIR/output-styles/` when configured). It preserves existing presets and settings. If the filename already exists, explain the collision and ask for a different name; do not overwrite their preset. On success, read its JSON `path` and `reference`, refresh the catalog and offer to activate the new preset (Step 3).

Only pass `"keep_coding_instructions": false` if the user explicitly wants to replace Claude Code's software-engineering instructions entirely (warn them that's what `false` does). Write their rules as clear imperatives: "Max 3 sentences per paragraph" beats "be concise".

If Python 3 is unavailable, write the same file directly: encode the name and description as quoted YAML strings, keep `keep-coding-instructions: true` by default, and create a new file without overwriting an existing path. Save only in the user's output-styles directory, never in this plugin, so their preset survives updates. Refresh the catalog to verify the exact name before offering activation.

## Guardrails

- Never set `force-for-plugin` on anything.
- Never modify the plugin's bundled style files.
- If a settings file contains invalid JSON, stop and show the user the problem instead of overwriting the file.
