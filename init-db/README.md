# Database Initialization

This directory contains SQL scripts that will be automatically executed when the PostgreSQL container starts for the first time.

## Usage

Place `.sql` or `.sh` files in this directory. They will be executed in alphabetical order when the PostgreSQL container initializes.

## Examples

- `01-init-extensions.sql` - Install PostgreSQL extensions
- `02-create-indexes.sql` - Create additional indexes
- `03-seed-data.sql` - Insert initial data

## Notes

- Scripts are only executed on the first run (when the database volume is empty)
- To re-run initialization scripts, remove the PostgreSQL volume:
  ```bash
  docker-compose down -v
  docker-compose up -d
  ```