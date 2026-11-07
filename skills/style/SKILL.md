---
name: style
description: Pick, switch, clear, or create a Claude Code output style. Use when the user invokes /lej-output-fixer:style, asks to change how Claude writes (tone, verbosity, readability, formatting), or mentions output styles.
---

# Output Style Picker

You are helping the user choose or create an output style. Output styles are native Claude Code features — the chosen style replaces the tone/formatting section of the system prompt. Your job: show a menu, apply the choice, confirm.

## Step 1 — Gather the options

Resolve the user's configuration directory once: use the nonempty `CLAUDE_CONFIG_DIR` environment variable when set, otherwise `~/.claude`. Call it **USER_CONFIG** below; it is a resolved path, not a new environment variable to persist. Use this same directory for user settings, user style discovery and preset creation. A custom profile must not read or edit the inactive `~/.claude` profile.

Use Claude Code's resolved catalog rather than maintaining a second list of style names. Check `claude --version` first. On v2.1.269 or newer, run this read-only local command from the current project directory:

```bash
claude --print --no-session-persistence --output-format json --plugin-dir "${CLAUDE_PLUGIN_ROOT}" /output-style
```

Read the JSON `result`: it lists the available built-in, plugin, user and project styles, their descriptions, and the current style. Keep each exact reference with its menu entry, including any plugin namespace. The catalog resolves names and precedence for this Claude Code version. Treat its `default` entry as **No output style**. Listing styles makes no model request; do not replace the command with a natural-language prompt.

On older versions, gather the catalog from files: read this plugin's `output-styles/*.md` under `${CLAUDE_PLUGIN_ROOT}` and its name from `.claude-plugin/plugin.json`; add the older built-ins Explanatory and Learning; then read user `USER_CONFIG/output-styles/` and project `.claude/output-styles/` files, including project directories between the working directory and repository root. Use frontmatter `name` and `description` when present; otherwise use the filename without `.md` as the name. Files without frontmatter are valid styles. For bundled entries, form `<plugin-name>:<style-name>` references; user and built-in entries use plain names.

Record the actual settings sources for this session and their `outputStyle` values: project-local overrides shared project overrides `USER_CONFIG/settings.json`. Do not assume the local file is relative to the working directory: current Claude Code can use the repository root, or the main checkout for a worktree, and also read a legacy local file in the starting directory. Follow the installed host's [settings-location rules](https://code.claude.com/docs/en/settings#where-claude-code-keeps-the-local-file-in-a-git-repository); identify the controlling file before editing or clearing it. Managed or session overrides may also win; do not change those to force a choice. The catalog can echo a configured reference that no longer exists: if that reference is absent from the available entries, explain that it is unavailable rather than marking it active.

## Step 2 — Present the menu

Prefer the AskUserQuestion tool. If it is unavailable or the user prefers text, present the same choices as a numbered list and accept a number or a short answer. Keep the exact catalog reference attached to each choice; the user need not type a namespaced reference.

- State the current selection in text before the menu, including when it is unavailable or overridden. Mark an available active style with the word "Current" in its description; do not rely on color, an icon or the initial highlighted option.
- AskUserQuestion allows max 4 options per question. Build one ordered list for this menu visit (bundled presets first, then the user's own, then the remaining entries). For a longer list, show up to two entries per page, plus **Previous page** and **Next page** only where those pages exist. State "Style choices, page X of Y" in the question. Keep the order and choice-to-reference mapping stable while paging; return to the same page when going back. Navigation does not select or write a style.
- Use distinct labels and short descriptions. If names need abbreviation, retain the full name in the description and disambiguate similar choices with their source when known. Use a simple list in the text fallback, without columns, decorative separators or animation. Host focus, wrapping, zoom and screen-reader announcements belong to Claude Code; do not claim to control them.
- The menu must always offer a path to two special entries:
  - **No output style** — return to Claude Code's default voice.
  - **Create new preset** — build a custom style (Step 4).

If the user dismisses the question or asks to cancel, stop without applying the highlighted option or changing settings. If the catalog changes before applying a choice, refresh it, explain any unavailable selection and ask again rather than choosing a substitute silently.
For an ambiguous or invalid text reply, clarify the choice without writing settings or making the user re-enter a full reference.

## Step 3 — Apply the choice

- **A style was chosen for the user profile**: write `"outputStyle": "<reference>"` into `USER_CONFIG/settings.json` (applies across projects using that profile). Re-read the file immediately before editing and preserve all existing keys with `jq` or a small `python3` round-trip, never a blind overwrite.
- **Only this project**: on v2.1.269+, use the same local command as Step 1 with `/output-style <reference>` as its single command argument, passing the exact selected reference as data, with proper argument quoting. This delegates the local-file location and JSON update to Claude Code. Check the JSON result for errors. On older hosts, edit only the actual project-local settings file identified in Step 1, preserving all other keys. Do not use the native selector for a user-wide choice: it saves at project-local scope.
- **The reference format matters.** Write the exact reference attached to the selected catalog entry in Step 1. Plugin styles need their namespace prefix (for example, `lej-output-fixer:Scannable`); bare plugin style names silently do nothing. Built-in and user-created styles use plain names. Do not reconstruct the reference from an abbreviated menu label.
- **Precedence check**: if a more-specific settings file already sets `outputStyle` (local overrides project overrides user), tell the user their choice won't take effect until that override is removed, and offer to remove it.
- **No output style**: remove only the `outputStyle` key from the identified user/project settings sources, re-reading each file before editing. Confirm with the user before touching a project-level file they may share with a team. Removing a higher-precedence key can expose another style underneath; recheck after each change. Do not delete presets or restore an old whole-file settings snapshot.
- **Confirm**: refresh the catalog on supported hosts and re-read the controlling settings sources. Distinguish the saved preference from the currently effective choice if an override remains; do not claim activation from a successful write alone. Note that if the change doesn't take effect immediately, starting a new session will pick it up.

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

The helper quotes metadata, keeps coding instructions by default, and creates a new file in `USER_CONFIG/output-styles/`. It preserves existing presets and settings. On success, read its JSON `path` and `reference` and say that the preset was saved. Separately refresh the catalog and controlling settings to report the effective selection: an existing setting may already name the newly available preset. Offer activation through Step 3 if needed; saving alone does not prove which style is effective. A filename rename does not change a frontmatter `name`; a deleted preset can leave a stale settings reference. Use the refreshed catalog rather than deriving a new reference from a filename or automatically repairing settings after an update or rollback.

### Recover without repeating the interview

Keep the agreed name, description, instructions and coding-instruction choice in this conversation until the user finishes or cancels. After a failed save, identify the affected field or file in plain text, explain the known correction and say whether a save was confirmed. A raw traceback or color alone is not the user-facing error. Do not start the interview over or ask for unchanged answers again.

- **Filename already exists**: explain that different names can use the same filename. Inspect that existing preset before suggesting another save: an earlier attempt may already have succeeded. Offer to use it if it matches the agreed content, change only the new preset's name while retaining the other answers, or cancel. Do not overwrite, delete or activate an existing preset as a side effect of recovery.
- **Invalid input**: name the field and the correction, such as a nonempty description or a one-line name. Ask only for that field and retain the other agreed answers.
- **Other save error or missing acknowledgement**: retain the answers and inspect the intended destination before retrying; do not claim the preset was saved or activated without evidence. Explain the observed failure and offer a retry after its cause is resolved, or cancel. If a complete matching preset is already present, refresh the catalog and offer activation instead of creating it again. Use the [recovery guide](../../RECOVERY.md) when more investigation is needed.

Before each retry, summarize just the correction and wait for the user's choice. After a confirmed save, refresh and report the effective selection, then offer activation with the exact reference if needed. If the user cancels, make no further writes; say whether a preset was already saved and that cancellation does not remove it. Do not promise recovery of interview answers across a closed session.

Only pass `"keep_coding_instructions": false` if the user explicitly wants to replace Claude Code's software-engineering instructions entirely (warn them that's what `false` does). Write their rules as clear imperatives: "Max 3 sentences per paragraph" beats "be concise".

If Python 3 is unavailable, write the same file directly: encode the name and description as quoted YAML strings, keep `keep-coding-instructions: true` by default, and create a new file without overwriting an existing path. Save only in `USER_CONFIG/output-styles/`, never in this plugin, so their preset survives updates. Refresh the catalog to verify the exact name before offering activation.

## Guardrails

- Never set `force-for-plugin` on anything.
- Never modify the plugin's bundled style files.
- If a settings file contains invalid JSON, stop and show the user the problem instead of overwriting the file.
