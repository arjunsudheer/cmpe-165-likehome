from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def start_scheduler():
    from backend.jobs.bookings import expire_bookings
    scheduler.add_job(expire_bookings, 'interval', minutes=5)
    scheduler.start()