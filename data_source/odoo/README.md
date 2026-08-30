# Odoo source service

This service runs Odoo Community 19.0 with PostgreSQL 15.

## Directory layout

- `odoo_source/`: local shallow checkout of the upstream Odoo 19.0 source.
  This directory is intentionally ignored by Git and is used for source
  inspection and debugging only.
- `custom_addons/`: project-owned Odoo modules. This directory is tracked by
  Git and is mounted into the container at `/mnt/extra-addons`.
- `config/odoo.conf`: Odoo runtime configuration.

The container installs the Odoo release pinned in `Dockerfile`; it does not run
directly from `odoo_source/`. This keeps the runtime reproducible while still
making the matching upstream source available locally.

## Refresh the local source checkout

From the repository root:

```bash
git clone --branch 19.0 --single-branch --depth 1 \
  https://github.com/odoo/odoo.git data_source/odoo/odoo_source
```

## Run

Create the shared network and start the service from the repository root:

```bash
docker network inspect end2end_data_network >/dev/null 2>&1 || \
  docker network create end2end_data_network

docker compose --env-file .env \
  -f data_source/odoo/docker-compose.odoo.yml \
  up -d --build
```

Open Odoo at `http://localhost:8070`.

After adding a module under `custom_addons/`, restart Odoo and update the Apps
list. A module can also be installed or upgraded from the command line with the
Odoo `-i` or `-u` option and the target database name.
