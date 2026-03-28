from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def start_scheduler():
    from backend.jobs.bookings import expire_bookings

    scheduler.add_job(expire_bookings, "interval", minutes=1, misfire_grace_time=120)
    scheduler.start()
