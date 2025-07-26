-- Create the user account
CREATE USER "user" WITH PASSWORD 'password';

-- Create the database
CREATE DATABASE bruno_ai_v2 OWNER "user";

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE bruno_ai_v2 TO "user";
