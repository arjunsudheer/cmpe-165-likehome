from dotenv import load_dotenv
import os

load_dotenv()

BASE_API_URL = "https://apidojo-booking-v1.p.rapidapi.com"

hotel_list_url = "/properties/v2/list"

hotel_details_url = "/properties/detail"

city_url = "/locations/auto-complete"

hotel_photos_url = "/properties/get-hotel-photos"

key = os.getenv("HOTEL_API_KEY")

headers = {
    "x-rapidapi-key": key,
    "x-rapidapi-host": "apidojo-booking-v1.p.rapidapi.com",
    "Content-Type": "application/json"
}