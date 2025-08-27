# Testing

This project does not include tests. Do not run test commands or attempt to install tools such as pytest or pyflakes, as you do not have permission to use the Internet. Additionally, refrain from referencing tests or their absence in commit messages or pull requests.

# Database Migrations

This project includes a SQLite database migration system.

- Migration files live in `jdbrowser/migrations` as numbered Python modules.
- Only modify the database through migrations. Do not change schema or seed data directly in application code or via ad‑hoc SQL.
- To make a change: add a new migration file with the next sequence number and implement `up(conn)` and `down(conn)`.
- Do not edit or reorder applied migrations; create a new migration for subsequent changes and commit it alongside the dependent code.
- Note: The `./db` helper script is for the maintainer’s workflow. Contributors do not need to use it; just add the migration file as described above.
