# LEJ Output Fixer

**Make Claude readable again.** Three ready-made output styles for Claude Code, plus a picker command. Works in the terminal and the Desktop app.

![A woman in an LEJ shirt relaxing at a clean studio desk, finally reading a screen that makes sense](assets/hero.png)

![Diagram: dense Claude output goes through LEJ Output Fixer and comes out readable, answer first](assets/what-it-does.svg)

<a id="install-it-in-under-a-minute"></a>

## Install it

Use [Claude Code](https://code.claude.com/docs/en/setup) in a terminal or the Desktop app's **Code** tab, with access to a local project. The regular Claude chat tab does not load this plugin. For the terminal commands, check that `claude --version` and `git --version` work first; sign in to Claude Code before using the picker. No repository build or package install is needed.

Paste this into your Claude Code session:

```
Install the lej-output-fixer plugin for me:
1. Run: claude plugin marketplace add justfinethanku/LEJ-output-fixer
2. Run: claude plugin install lej-output-fixer@lej
Then start a fresh session, run /lej-output-fixer:style, and help me pick a style.
```

Claude runs the two commands. Start a fresh session before opening the picker; installing the plugin does not select a style.

To install from a terminal, run these two commands in order:

```bash
claude plugin marketplace add justfinethanku/LEJ-output-fixer
```

```bash
claude plugin install lej-output-fixer@lej
```

Check the installation:

```bash
claude plugin list
claude plugin details lej-output-fixer@lej
```

Expect `lej-output-fixer@lej` to be enabled and its details to list the `style` skill. The picker offers the three bundled output styles. Open a fresh Claude Code session and run `/lej-output-fixer:style` there. The slash command belongs in the session, not your shell.

## Why this exists

You ask Claude a question. You get back a wall of text... dense, jargon-packed, zero paragraph breaks. You read it twice and you're still not sure what the actual answer was.

![A woman in an LEJ shirt staring skeptically at a monitor showing one giant unbroken wall of text](assets/the-problem.jpeg)

Here's the thing: Claude Code already ships with a fix. It's called an output style, and it swaps out the part of Claude's instructions that controls tone and formatting. Not a suggestion layered on top... a real replacement, built into the product.

In the terminal, `/config` has an Output style menu. Claude Code v2.1.269 and newer also supports `/output-style` to list or switch styles. This plugin adds a guided picker with preset creation, including for local Desktop Code sessions.

So this plugin puts a door on it. Three styles that fix the actual complaints, and one command that lets you switch, turn them off, or build your own.

## The three styles

![A woman in an LEJ shirt choosing between three cards labeled Scannable, Bottom Line, and Walk Me Through](assets/pick-a-style.jpeg)

**Scannable**: Answer first, short paragraphs, 8th-grade reading level, jargon spelled out. For when you're smart but busy and Claude keeps handing you homework.

**Bottom Line First**: Executive brief mode. The verdict up top, then only the details that would change a decision. Numbers over adjectives.

**Walk Me Through It**: Claude does the work at full quality but narrates it: says what it's about to do, defines every term, explains what happened in plain cause-and-effect. For when the territory is new to you.

All three keep Claude Code's coding instructions fully intact. They change how Claude talks, never how well it codes.

## Using it

Run:

```
/lej-output-fixer:style
```

You get a menu: the three styles above, any styles you've made yourself, **No output style** to go back to stock Claude, and **Create new preset**.

Pick one to save it for projects using your active user profile on this machine. A project's own `outputStyle` setting takes precedence; the picker points out an override and offers to remove it. You can also ask to apply a style only to the current project. Other machines and cloud sessions have separate settings. Switching and turning styles off use the same command again.

## Build your own style

Pick **Create new preset** from the menu and Claude interviews you: what should it be called, how formal, how long-winded, what formatting you want, what habits drive you nuts. It writes the style file to your own `~/.claude/output-styles/` folder and offers to turn it on. If you use `CLAUDE_CONFIG_DIR`, new presets go in that directory's `output-styles/` instead. Python 3 enables the preset-saving helper; the picker has a direct-file fallback when Python is unavailable.

Your custom styles belong to you, not to this plugin. Updates and uninstalls never touch them.

## Good to know

- **Nothing activates on install.** Claude Code records that the plugin is enabled, but leaves your `outputStyle` selection unchanged.
- **Style selection changes one field.** Picking a style writes `outputStyle` in your user settings (`~/.claude/settings.json` by default), or the host's project-local settings file for a project-only choice. `CLAUDE_CONFIG_DIR` selects a custom user profile when set; project-local settings can live at the repository root or main checkout of a linked worktree. Other settings stay in place. Creating a preset also adds its Markdown file.
- **New sessions pick up changes.** If a style switch doesn't kick in mid-session, start a fresh session and it's there.

## Update or uninstall

To fetch the latest listing and update your installed copy, run:

```bash
claude plugin marketplace update lej
claude plugin update lej-output-fixer@lej
```

Start a fresh session afterward. Your custom presets remain in your user directory.

Before uninstalling, run `/lej-output-fixer:style` and choose **No output style**, or select a built-in or custom style you want to keep. Then run this in your terminal:

```bash
claude plugin uninstall lej-output-fixer@lej
```

Uninstall removes the plugin but does **not** remove an `outputStyle` value you selected earlier or restore a previous style. Custom presets remain yours. If you already uninstalled, remove the unavailable `lej-output-fixer:…` value from the `outputStyle` field in your settings, preserving the other JSON keys, or select an available style through `/config`. Check project settings for overrides too.

For collisions, renamed or deleted presets, overlapping settings and a verified-ref rollback, follow [Recover a missing or renamed output style](RECOVERY.md).

## Troubleshoot

- **`claude: command not found`**: install the [Claude Code CLI](https://code.claude.com/docs/en/setup), reopen your terminal, and check `claude --version`.
- **Picker missing after install**: check `claude plugin list` in the same local environment, confirm the plugin is enabled, then start a fresh session. Use Desktop's Code tab, not regular chat.
- **Style stays unchanged**: identify the active profile and actual project settings sources as described in the [recovery guide](RECOVERY.md#identify-the-active-profile-and-selection). Check for an `outputStyle` override. Bundled styles require their exact reference, such as `lej-output-fixer:Scannable`; `Scannable` alone does not select this plugin's style. Preserve other settings when editing JSON.
- **Style disappeared after uninstall**: clear the leftover reference as described in [Update or uninstall](#update-or-uninstall). To see available styles on Claude Code v2.1.269+, run `/output-style` in a session; older terminal versions have `/config`.
- **Invalid settings JSON or an existing preset name**: fix the JSON error or choose another preset name. The picker does not replace a broken settings file or overwrite an existing preset.

Install, update, catalog discovery, settings precedence, and uninstall behavior were checked with Claude Code **2.1.318** on Linux. The Desktop GUI and a live model following the picker interview were not exercised in that check. See the current [plugin management](https://code.claude.com/docs/en/discover-plugins), [output-style](https://code.claude.com/docs/en/output-styles), and [settings](https://code.claude.com/docs/en/settings) documentation for host behavior.

## Credit

Built by [Jonathan Edwards](https://github.com/justfinethanku). The styles exist because good answers you can't read aren't good answers.

MIT licensed. Take it, fork it, make your own presets.
