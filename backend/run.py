from app import create_app
from db_connection import engine, Base

app = create_app()

Base.metadata.create_all(engine)


if __name__ == "__main__":
    app.run(debug=True)
