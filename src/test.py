import requests
import config


def query_TFL(url: str, params: dict, max_retries: int = 3):

    for retry_attempt in range(max_retries):
        try:
            response = requests.get(url, params=params).json()
            if response:
                return response
            else:
                raise ValueError("Error Communicating with TFL")
        except ValueError:
            if retry_attempt == 2:
                raise RuntimeError("Failed to fetch station ID after 3 retries.")


def get_station_id():

    TFL_STOPPOINT_SEARCH_URL = "https://api.tfl.gov.uk/StopPoint/Search"  # TFL API endpoint for searching stop points with name that matches the query

    params = {
        "query": config.station,  # user defined station name
        "modes": config.mode,  # user defined mode (e.g., tube, bus, etc.)
        "maxResults": 1,  # return only best match
        "api_key": config.api_key,  # user defined API key
    }

    response = query_TFL(TFL_STOPPOINT_SEARCH_URL, params)

    return {"id": response["matches"][0]["id"], "name": response["matches"][0]["name"]}


print(get_station_id())  # This will print the station ID and name if successful
