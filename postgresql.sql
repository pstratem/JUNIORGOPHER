BEGIN;
CREATE TABLE sensors(id uuid PRIMARY KEY, label text);
CREATE TABLE cameras(id uuid PRIMARY KEY REFERENCES sensors(id), url text not null, location text);
CREATE TABLE segments(id uuid PRIMARY KEY, camera_id uuid REFERENCES cameras(id), start timestamp with time zone, stop timestamp with time zone);
CREATE TABLE events(id uuid PRIMARY KEY, sensor_id uuid REFERENCES sensors(id), start timestamp with time zone, stop timestamp with time zone);
COMMIT;
