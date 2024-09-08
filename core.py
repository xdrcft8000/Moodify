import os
from fastapi import FastAPI, Request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware


if os.environ.get('ENVIRONMENT') != 'production':
    from dotenv import load_dotenv
    load_dotenv()

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Add your SvelteKit dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')  # Ensure this environment variable is correctly set¬
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()