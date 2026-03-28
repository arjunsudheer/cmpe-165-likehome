from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Used for removing the INPROGRESS state from hotel blocking during the checkout timer
# Without this, the hotels will stay blocked even after the timer expires
def start_scheduler():
    from backend.jobs.bookings import expire_bookings

    scheduler.add_job(expire_bookings, "interval", minutes=1, misfire_grace_time=120)
    scheduler.start()
