from backend import create_app
from backend.scheduler import start_scheduler

app = create_app()

# Start the background job that cancels expired INPROGRESS bookings every 5 min
start_scheduler()

if __name__ == "__main__":
    app.run(debug=True)
