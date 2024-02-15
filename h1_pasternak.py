import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json

API_TOKEN = ""
RSA_KEY = ""

app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

def generate_weather(location: str, date: str):
    url_base = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    key = RSA_KEY
    url = f"{url_base}/{location}/{date}?unitGroup=metric?&key={key}"

    headers = {"X-Api-Key": RSA_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == requests.codes.ok:
        weather_data = json.loads(response.text)
        print(weather_data) 

        humidity = weather_data["days"][0]["humidity"]
        if humidity > 60:
            forecast = "you should take an umbrella"
        else:
            forecast = "you don't need an umbrella"

        sunrise_time = weather_data["days"][0]["sunrise"]
        sunset_time = weather_data["days"][0]["sunset"]

        feels_like = weather_data["days"][0]["feelslike"]
        temp_actual = weather_data["days"][0]["temp"]
        temp_max = weather_data["days"][0]["tempmax"]
        temp_min = weather_data["days"][0]["tempmin"]

        temp_diff_feels_like = feels_like - temp_actual
        temp_diff_max = temp_max - temp_actual
        temp_diff_min = temp_actual - temp_min

        weather_info = {
            "temp": temp_actual,
            "temp_diff_max": temp_diff_max,
            "temp_diff_min": temp_diff_min,
            "feelslike": feels_like,
            "temp_diff_feels_like": temp_diff_feels_like,
            "wind_kph": weather_data["days"][0]["windspeed"],
            "pressure_mb": weather_data["days"][0]["pressure"],
            "humidity": humidity,
            "magical forecast": forecast,
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "the_sun_shines": calculate_time_difference(sunrise_time, sunset_time),
            
        }

        return weather_info
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)

def calculate_time_difference(start_time, end_time):
    start_datetime = datetime.strptime(f'{datetime.now().date()} {start_time}', "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(f'{datetime.now().date()} {end_time}', "%Y-%m-%d %H:%M:%S")

    time_difference = end_datetime - start_datetime
    return str(time_difference)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/forecast", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    requester = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")

    if not location or not date:
        raise InvalidUsage("location and date are required", status_code=400)

    weather_data = generate_weather(location, date)


    result = {
        "requester_name": requester,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "location": location,
        "date": date,
        "weather": weather_data,
    }

    return result

if __name__ == '__main__':
    app.run(debug=True)