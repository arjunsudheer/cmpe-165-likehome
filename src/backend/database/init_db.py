from db_connection import engine, Base
import models

def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)

if __name__ == "__main__":
    init_tables_and_data()