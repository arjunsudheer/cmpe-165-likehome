# cmpe-165-likehome
This repository is dedicated to the LikeHome Project from the CMPE 165 class at SJSU.

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
    python app.py
    ```
    
