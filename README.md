# cmpe-165-likehome
This repository is dedicated to the LikeHome Project from the CMPE 165 class at SJSU.


# Running the Application

## With Docker

1. Create your own ```.env``` by referencing ```.env.example```
    - Only for the following variables, use these values:
        ```.env
        DB_HOST=db
        DB_PORT=5432
        ```
        
2. Run the application:
```sh
docker compose up -d --build
```

# Manual Setup

## Backend Setup

1. Go to backend folder: 
    ```sh
    cd backend
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Create your own ```.env``` by referencing ```.env.example```

4. To test the hotel details endpoint 
    - seed the data to populate the tables
    ```sh
    python backend/init_db.py
    ```

5. Run the server: 
    ```sh
    python -m backend.app
    ```

## Frontend Setup

1. Go to frontend folder: 
    ```sh
    cd frontend
    ```

2. Install the required dependencies:
    ```sh
    npm install
    ```
    
3. Run the frontend server: 
    ```sh
    npm run dev
    ```
