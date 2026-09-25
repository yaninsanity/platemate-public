# Security Policy

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**), which opens a channel visible only to
the maintainers.

Include what you can: the affected version or commit, what an attacker gains,
and the steps to reproduce it. A proof of concept helps but is not required to
start the conversation.

Expect an acknowledgement within a week. Please give us a reasonable window to
ship a fix before disclosing publicly.

## Scope

In scope: this repository's code and its default configuration.

Out of scope: vulnerabilities in third-party dependencies (report those
upstream), and anything that requires an attacker to already control the server
or the database.

## Handling credentials

Credentials never belong in this repository. `backend/.env` is ignored by git
and `.githooks/pre-commit` refuses to commit credential files or key-shaped
strings.

If you do commit a secret, **rotate it first**. Rewriting history does not make
a leaked credential safe; the value has to be replaced at the provider.
