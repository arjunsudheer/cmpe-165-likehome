from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Used for removing the INPROGRESS state from hotel blocking during the checkout timer
# Without this, the hotels will stay blocked even after the timer expires
def start_scheduler():
    from backend.jobs.bookings import expire_bookings, complete_bookings_and_earn_points, create_booking_reminders

    scheduler.add_job(expire_bookings, "interval", minutes=1, misfire_grace_time=120)
    scheduler.add_job(complete_bookings_and_earn_points, "cron", hour=0, minute=0, timezone="UTC")
    scheduler.add_job(create_booking_reminders, "interval", minutes=1, misfire_grace_time=60)
    scheduler.start()
