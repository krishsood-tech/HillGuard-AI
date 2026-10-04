-- HillGuard AI schema (PostgreSQL + PostGIS)
-- For SQLite local demo the SQLAlchemy models create equivalent tables without geometry types.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'USER',
  display_name VARCHAR(120),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incidents (
  id UUID PRIMARY KEY,
  category VARCHAR(64) NOT NULL,
  description TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  geometry geometry(Point, 4326),
  location_label VARCHAR(255),
  observed_at TIMESTAMPTZ NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source VARCHAR(64) NOT NULL DEFAULT 'community',
  verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified',
  image_url VARCHAR(512),
  contact_ref VARCHAR(120),
  reviewer_notes TEXT,
  reviewed_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incidents_geom_gix ON incidents USING GIST (geometry);
CREATE INDEX IF NOT EXISTS incidents_status_idx ON incidents (verification_status);
CREATE INDEX IF NOT EXISTS incidents_category_idx ON incidents (category);

CREATE TABLE IF NOT EXISTS external_observations (
  id UUID PRIMARY KEY,
  source VARCHAR(120) NOT NULL,
  observation_type VARCHAR(64) NOT NULL,
  location_label VARCHAR(255),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  observed_at TIMESTAMPTZ,
  retrieved_at TIMESTAMPTZ NOT NULL,
  value JSONB,
  units VARCHAR(64),
  source_url VARCHAR(512),
  license VARCHAR(255),
  quality_flag VARCHAR(32),
  is_demo BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS routes (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  start_label VARCHAR(255),
  end_label VARCHAR(255),
  geometry_json TEXT,
  source VARCHAR(64),
  status VARCHAR(32),
  last_verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_outputs (
  id UUID PRIMARY KEY,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  target VARCHAR(64) NOT NULL,
  time_window VARCHAR(64),
  category VARCHAR(32),
  score DOUBLE PRECISION,
  uncertainty VARCHAR(64),
  model_version VARCHAR(64) NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL,
  input_coverage VARCHAR(64),
  explanation JSONB,
  is_demo BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS audit_records (
  id UUID PRIMARY KEY,
  action VARCHAR(64) NOT NULL,
  entity VARCHAR(64) NOT NULL,
  entity_id VARCHAR(64),
  actor_id UUID,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  previous_state JSONB,
  new_state JSONB
);

CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY,
  user_id UUID,
  kind VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  is_official BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  read_at TIMESTAMPTZ
);
