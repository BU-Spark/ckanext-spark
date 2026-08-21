-- Datastore database + read-only role, created on the Postgres container's
-- first boot. CKAN's datastore plugin refuses to start without both, and the
-- read URL must be a genuinely separate role or a SQL-injected datastore query
-- could reach the main CKAN tables.
CREATE ROLE datastore_ro NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN PASSWORD 'pass';
CREATE DATABASE datastore OWNER ckan ENCODING 'utf-8';
