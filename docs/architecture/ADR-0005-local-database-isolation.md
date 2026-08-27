# ADR-0005 — Local Database Isolation

Status: Accepted

The developer workstation already operates a stable native PostgreSQL 17 server. ISI therefore uses that server for local development instead of creating a parallel Docker PostgreSQL instance.

Local database contract:

- server: `localhost:5432`;
- database: `isi`;
- application role: `isi_app`;
- existing databases such as `krcuga`, `oralscan`, `simpa`, and `incluscape` remain independent and untouched;
- schema evolution is performed only through ISI Alembic migrations.

The application role is intentionally not a superuser and does not receive database-creation or role-creation privileges. Administrative bootstrap uses the workstation's existing PostgreSQL administrator only to create the isolated ISI role/database.
