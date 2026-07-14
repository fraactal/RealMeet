import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql+pg8000://realmeet:realmeet@localhost:25432/realmeet")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:15173"]')
