# Recover a missing or renamed output style

Use this guide when a preset save collides with an existing file, a renamed or deleted style stops applying, or you need to recover after a plugin update. You need access to your local Claude Code settings. Terminal examples require Claude Code v2.1.269+; use `/config` on older versions.

## Identify the active profile and selection

1. Use the same terminal environment and project directory as the affected session. When `CLAUDE_CONFIG_DIR` is nonempty, that directory owns your user settings and `output-styles/`. Otherwise, use `~/.claude`. Leave an inactive profile alone.
2. List the host's available styles from that project:

   ```bash
   claude --print --no-session-persistence --output-format json /output-style
   ```

   Read the JSON `result`. Compare the configured style in its header with the available entries. A header naming a deleted style does not mean that style loaded. This local command makes no model request.
3. Identify each settings file that sets `outputStyle`. Among user and project files, local project settings override shared project settings, which override user settings. The local file can belong to the repository root or the main checkout of a linked worktree; it is not always relative to your current directory. Follow the host's [settings-location rules](https://code.claude.com/docs/en/settings#where-claude-code-keeps-the-local-file-in-a-git-repository). Check `/status` in the affected session for managed settings or session overrides too.

Keep a copy of any file you plan to edit for comparison. Use the current file when making an edit: restoring an older whole settings file can erase newer permission, plugin or preference changes.

## Resolve an existing preset filename

The saver turns a style name into a filename. Different names can produce the same filename: `My Brief` and `My/Brief` both use `my-brief.md`. An existing destination causes the save to fail without replacing that file.

1. Read the existing file at the error's path in your active profile. Check its frontmatter `name`, description and complete instruction body. A previous save might already have succeeded, including when an acknowledgement was interrupted.
2. If it is the preset you want, use its exact available reference from the catalog. Do not retry creation just to activate it.
3. To keep both presets, choose a name that also produces a different filename, such as `My Brief v2`, then create it again through the picker.

If an old, interrupted save left an empty or incomplete `.md` file, preserve a copy outside `output-styles/` before moving that particular file out and retrying. Current saves publish a complete file without replacing an existing destination. Ignored `.preset-*.tmp` files are not catalog entries; deleting all styles or all staging files is not a recovery step.

## Rename or retire a custom style

The frontmatter `name` is the style reference when present. Renaming `my-brief.md` to `archived-brief.md` keeps the reference `My Brief`. Renaming a file also frees its old filename for another preset; an old retry can then collide with that newer preset.

1. To change the menu name, edit the `name` in your own preset's frontmatter to a unique name. Preserve its description, instructions and `keep-coding-instructions: true`. Leave bundled files in the plugin alone.
2. Start a fresh session or repeat the catalog command to discover the new exact reference. Review other user and project presets if the name is already present.
3. Select that reference through `/lej-output-fixer:style`. For a project-only selection, the native terminal command is:

   ```bash
   claude --print --no-session-persistence --output-format json '/output-style My Brief v2'
   ```

   Replace `My Brief v2` with the exact catalog reference, keeping the whole slash command as one quoted argument. This writes the host's project-local settings, not your user-wide preference. Check the JSON result for an error. For a user-wide choice, use the plugin picker and confirm that it uses the active profile.
4. Before retiring a preset, select another available style or choose **No output style** through the picker. Then move only your unwanted preset out of the style directory. If it was already deleted, remove only its stale `outputStyle` key from the controlling settings file, preserving every other key.

After each removal, check the catalog and the remaining settings sources again. For example, clearing a local choice can expose a shared project choice; clearing that can expose a user choice. To return to default, remove the unwanted selections from all applicable user/project sources. Agree with your team before changing a shared project file. Do not delete presets to clear a preference.

## Recover after an update

From the affected environment, inspect the installed version and scope:

```bash
claude plugin list
claude plugin details lej-output-fixer@lej
```

For the README's user-scoped install, refresh and update with:

```bash
claude plugin marketplace update lej
claude plugin update lej-output-fixer@lej --scope user
```

Use the listed scope if yours differs. Start a fresh session and check the catalog. Updating plugin code does not repair stale style references, rename your custom styles or clear project overrides. A repeated update also leaves those selections in place. Resolve them with the procedures on this page.

### Roll back a user-scoped installation

Use this procedure only for a previously reviewed Git ref and a sole user-scoped installation from the `lej` marketplace. It replaces that marketplace registration; check for project/local installations and shared marketplace declarations first. Other scopes need their own host-specific recovery. Record the current source, version and scope with `claude plugin marketplace list` and `claude plugin list` before starting.

Prepare the source before removing the installed copy. From your project directory, clone into a new, unused `LEJ-output-fixer-rollback` directory. Replace `VERIFIED_COMMIT` with the full commit SHA you reviewed:

```bash
git clone --no-checkout https://github.com/justfinethanku/LEJ-output-fixer.git LEJ-output-fixer-rollback
git -C LEJ-output-fixer-rollback checkout --detach VERIFIED_COMMIT
git -C LEJ-output-fixer-rollback rev-parse HEAD
```

Confirm that the printed SHA matches the intended commit. Keep this checkout available while it is registered as your marketplace. The GitHub marketplace `#ref` syntax accepts branches or tags on this host; a raw commit SHA fails during clone. The local checkout supports an exact commit. This changes plugin code, not the Claude Code host version.

Then replace the user-scoped installation:

```bash
claude plugin uninstall lej-output-fixer@lej --scope user
claude plugin marketplace remove lej
claude plugin marketplace add ./LEJ-output-fixer-rollback
claude plugin install lej-output-fixer@lej --scope user
```

Run the commands in order, stopping if any fails. Check the installed version and available styles before resuming. Custom preset bytes and existing `outputStyle` values remain in place, including unavailable selections; rollback does not restore old settings. Keep newer unrelated edits and resolve stale selections separately. Older plugin code can lack current saver and profile fixes, so check that release's behavior before using its picker to write settings.

To return to the latest release, repeat the four plugin commands with `justfinethanku/LEJ-output-fixer` as the marketplace source instead of `./LEJ-output-fixer-rollback`. Verify the version, start a fresh session and check the catalog again. If removal succeeded but adding or installing failed, resume at that failed command rather than restoring old settings or deleting custom presets.

## Verification limits

These procedures were executed with Claude Code **2.1.319** on Linux in disposable custom profiles with overlapping user/shared/local selections, renamed and deleted presets, unrelated newer edits and an inactive default profile. Update used actual v1.0.3 and v1.0.6 source in a local marketplace. A GitHub clone checked out at the historical commit, local marketplace rollback and return to the latest GitHub release were checked separately. Direct GitHub marketplace registration with a raw commit SHA failed; that path is excluded from the procedure. No live model picker conversation, Desktop GUI, Windows, older host, managed-policy change or concurrent settings writer was exercised.

See the host's [output style reference](https://code.claude.com/docs/en/output-styles) and [plugin management guide](https://code.claude.com/docs/en/discover-plugins) for current commands and settings behavior.
