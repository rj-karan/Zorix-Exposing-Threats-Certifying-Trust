CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

DO $$
BEGIN
  RAISE NOTICE 'Zorix database initialized successfully';
END $$;