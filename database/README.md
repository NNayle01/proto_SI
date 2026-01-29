# Database Initialization

This directory contains the database dump for automatic initialization of the Dolibarr database.

## Files

- `init-dolibarr.sql` - Complete database dump including:
  - All products and categories
  - Dolibarr configuration and modules
  - Users and permissions
  - Stock levels
  - Sample data

## How It Works

When you start the project for the first time using `docker compose up`, the MariaDB container automatically imports `init-dolibarr.sql` into the database. This gives you a fully configured Dolibarr instance with:

✅ All products loaded  
✅ E-commerce modules configured  
✅ API enabled and ready  
✅ Admin account created  

## Manual Export

To create a fresh database dump (for example, after adding new products):

```bash
./scripts/export-database.sh
```

This will update the `init-dolibarr.sql` file with the current database state.

## Starting Fresh

If you want to reset the database to the initial state:

```bash
# Stop all containers and remove volumes
docker compose down -v

# Start again (will re-import the SQL file)
docker compose up -d
```

## File Size

The database dump is approximately 1.6MB compressed with all sample data.
