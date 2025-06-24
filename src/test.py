import config
import json
import requests
import time


def query_TFL(
    url: str,
    params: dict = None,
    max_retries: int = 3,
    _session: requests.Session = None,
) -> list:
    session_to_use = _session if _session else requests.Session()
    for retry_attempt in range(max_retries):
        try:
            response = session_to_use.get(url, params=params, timeout=10)
            response.raise_for_status()
            json_response = response.json()
            return json_response if json_response else []
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(
                f"Error calling TfL API (Attempt {retry_attempt + 1}/{max_retries}): {e}"
            )
            if retry_attempt == max_retries - 1:
                raise RuntimeError(
                    f"Failed to fetch data from {url} after {max_retries} retries: {e}"
                )
        time.sleep(1)
    return []


vehicle_id = "025"
url1 = "https://api.tfl.gov.uk/Vehicle/" + vehicle_id + "/Arrivals"


url2 = "https://api.tfl.gov.uk/StopPoint/Search"
params2 = {
    "query": "victoria",
    "modes": "tube",
    "maxResults": 1,
    "app_key": config.api_key,
}

station_id_monument = "940GZZLUMMT"
station_id_victoria = "HUBVIC"
station_id_chiswickpark = "940GZZLUCWP"
url3 = "https://api.tfl.gov.uk/StopPoint/" + station_id_chiswickpark + "/Arrivals"

params = {
    "app_key": config.api_key,
}

print(params)
response = query_TFL(url1, params)
print(json.dumps(response, indent=2))
