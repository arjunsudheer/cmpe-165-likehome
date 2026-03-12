from backend.app import create_app
from backend.database.db_connection import engine, Base

app = create_app()

Base.metadata.create_all(engine)


if __name__ == "__main__":
    app.run(debug=True)