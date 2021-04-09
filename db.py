import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

DB_ENGINE = os.environ.get("DB_ENGINE")

engine = create_engine(DB_ENGINE if DB_ENGINE is not None 
        else 'sqlite+pysqlite:///:memory:', echo=True, future=True)

Base = declarative_base()

class School(Base):

    __tablename__ = "woot"

    id = Column(Integer, primary_key=True)
    name = Column(String)  


    def __init__(self, name):

        self.name = name    


Base.metadata.create_all(engine)