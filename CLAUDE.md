# scp-civics

A public Claude Code plugin for St. Charles Parish, Louisiana civic research. If `.context/README.md` exists, read it first; `.context/` is private and never committed.

## What may be published

Every commit is public from the moment it is pushed, and history is hard to take back.

- **Allowed:** public officials acting in office, their office contacts, parish records and their citations, public companies and applicants named in public records.
- **Not allowed:** a requester's home address, phone or personal email, and their requests, request numbers, case files or strategy; private landowners' names outside verbatim government record titles; local machine paths; employer or network details.
- A skill should say how something works in general. A specific case belongs in `.context/` or in the user's own project folder.

Run `scripts/check-public.sh` before committing. The `pre-commit` hook runs it if installed with `scripts/install-hooks.sh`. After changing a skill, also run `claude plugin validate .claude-plugin/plugin.json`: a frontmatter parse error otherwise only shows up as a skill silently losing its metadata. Warnings about `CLAUDE.md` and `CLAUDE.local.md` at the root are expected.

## Conventions

- Skills live in `skills/<name>/SKILL.md`, with helpers in `scripts/` and `references/`. Refer to helpers through `${CLAUDE_PLUGIN_ROOT}/skills/<name>/...`.
- Refer to sibling skills as `scp-civics:<name>`.
- `bayou:` skills are optional. Any skill that names one must also say what to do without bayou.
- Source PDFs and downloaded attachments are not published. Local copies are reached through `$SCP_CIVICS_DATA`; handle it being unset. The drainage corpus in `corpus/` is read-only except through `--add`.
- Date perishable facts ("as of 2026-11-02"), separate what is established from what is not, and cite the source.
- Skills draft and research. They never send a request, file a comment or make a purchase.
- `references/status-ledger.md` is generated: edit `scripts/status_ledger_md.py` or `scripts/status_build.py`, then rebuild.
