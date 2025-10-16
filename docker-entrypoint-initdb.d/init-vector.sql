-- docker-entrypoint-initdb.d/init-vector.sql
DO $$
BEGIN
    RAISE NOTICE 'Initializing vector extension...';
    CREATE EXTENSION IF NOT EXISTS vector;
    RAISE NOTICE 'Vector extension initialized.';
END $$;