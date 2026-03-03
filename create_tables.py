import os
from dotenv import load_dotenv
load_dotenv('.env')

from sqlalchemy import create_engine
from src.models import Base

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
print("Tables created successfully.")
