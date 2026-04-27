# cmpe-165-likehome
This repository is dedicated to the LikeHome Project from the CMPE 165 class at SJSU.

## Running the Application

First, create your own ```.env``` file by referencing ```.env.example```. Place your ```.env``` file in the root directory of this project.

Important for local setup:
- The backend reads `DATABASE_URL` from the root `.env`.
- The frontend only needs a separate `frontend/.env` if you want Google sign-in while running `npm run dev` manually.

### Docker Setup

Refer to the following commands when using Docker.

```sh
# First time (or after code changes)
docker compose up --build

# Subsequent starts (no code changes)
docker compose up

# Stop everything (data volume is preserved)
docker compose down

# Stop AND wipe the database volume (fresh start)
docker compose down -v
```

## Manual Setup

### Backend Setup

Run these commands only once for set up:

```sh
# Go to the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Make sure your local PostgreSQL server is running and that the database
# from DATABASE_URL in the root .env already exists.
#
# Populate the database
cd ../
python -m backend.db.init_db
```

To start the backend server, run the following command:

```sh
python -m backend.app
```

### Frontend Setup

Run these commands only once for set up:

```sh
# Go to the frontend directory
cd frontend

# Install dependencies
npm install
```

If you want Google sign-in while running the frontend manually, create `frontend/.env`
from `frontend/.env.example` and set:

```sh
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

To start the frontend server, run the following command:

```sh
npm run dev
```
