import requests


# =========================================================
# COUNTRY CODE HELPER
# =========================================================

def get_country_code(country):
    """
    Convert common country names into ISO country codes.
    """

    country_codes = {
        "india": "IN",
        "italy": "IT",
        "usa": "US",
        "united states": "US",
        "uk": "GB",
        "united kingdom": "GB",
        "france": "FR",
        "germany": "DE",
        "japan": "JP",
        "uae": "AE",
        "united arab emirates": "AE",
        "canada": "CA",
        "australia": "AU",
        "spain": "ES",
        "singapore": "SG",
        "nepal": "NP",
        "thailand": "TH"
    }

    return country_codes.get(
        country.strip().lower()
    )


# =========================================================
# FIND LOCATION
# =========================================================

def find_location(city):
    """
    Find the correct city using Open-Meteo geocoding.

    Handles input such as:
        Goa
        Goa, India
        Mumbai, India
        Paris, France
    """

    parts = [
        part.strip()
        for part in city.split(",")
    ]

    city_name = parts[0]

    country_code = None

    if len(parts) > 1:
        country_code = get_country_code(parts[1])

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )

    geo_params = {
        "name": city_name,
        "count": 20,
        "language": "en",
        "format": "json"
    }

    # Add country filter when available
    if country_code:
        geo_params["countryCode"] = country_code

    try:

        response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:

        return {
            "error": f"Location lookup failed: {e}"
        }

    results = data.get(
        "results",
        []
    )

    if not results:

        return {
            "error": f"Could not find destination: {city}"
        }

    # -----------------------------------------------------
    # FIND EXACT CITY
    # -----------------------------------------------------

    city_lower = city_name.lower()

    exact_matches = []

    for result in results:

        result_name = result.get(
            "name",
            ""
        ).lower()

        if result_name == city_lower:
            exact_matches.append(result)

    # -----------------------------------------------------
    # IF COUNTRY WAS PROVIDED
    # PREFER THE CORRECT COUNTRY
    # -----------------------------------------------------

    if country_code:

        country_matches = []

        for result in exact_matches:

            result_country = result.get(
                "country_code",
                ""
            ).upper()

            if result_country == country_code:

                country_matches.append(result)

        if country_matches:

            results_to_use = country_matches

        else:

            results_to_use = []

    else:

        results_to_use = exact_matches

    # -----------------------------------------------------
    # SPECIAL CASE:
    # INDIA DESTINATIONS
    # -----------------------------------------------------

    if (
        city_lower == "goa"
        and country_code == "IN"
    ):

        # Goa is a state, but Open-Meteo may return
        # unrelated places named Goa.
        #
        # We want a location actually inside Goa.

        for result in results:

            admin1 = result.get(
                "admin1",
                ""
            ).lower()

            result_country = result.get(
                "country_code",
                ""
            ).upper()

            if (
                result_country == "IN"
                and admin1 == "goa"
            ):

                return result

        # Known geographic center of Goa
        # used only if geocoding gives no suitable Goa.

        return {
            "name": "Goa",
            "country": "India",
            "country_code": "IN",
            "admin1": "Goa",
            "latitude": 15.2993,
            "longitude": 74.1240,
            "elevation": 50,
            "timezone": "Asia/Kolkata",
            "feature_code": "ADM1"
        }

    # -----------------------------------------------------
    # NORMAL DESTINATION SELECTION
    # -----------------------------------------------------

    if results_to_use:

        return results_to_use[0]

    # If no exact match, use first result
    return results[0]


# =========================================================
# TOOL 1: CHECK WEATHER
# =========================================================

def check_weather(city):
    """
    Get current weather using Open-Meteo.
    """

    location = find_location(city)

    if "error" in location:

        return location

    latitude = location.get(
        "latitude"
    )

    longitude = location.get(
        "longitude"
    )

    city_name = location.get(
        "name",
        city
    )

    country = location.get(
        "country",
        "Unknown"
    )

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    weather_params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        )
    }

    try:

        response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        response.raise_for_status()

        weather_data = response.json()

    except requests.RequestException as e:

        return {
            "error": f"Weather API request failed: {e}"
        }

    current = weather_data.get(
        "current"
    )

    if not current:

        return {
            "error": "Could not retrieve current weather."
        }

    return {

        "city": city_name,

        "country": country,

        "temperature":
            current.get(
                "temperature_2m"
            ),

        "humidity":
            current.get(
                "relative_humidity_2m"
            ),

        "precipitation":
            current.get(
                "precipitation"
            ),

        "weather_code":
            current.get(
                "weather_code"
            ),

        "wind_speed":
            current.get(
                "wind_speed_10m"
            )
    }


# =========================================================
# TOOL 2: CHECK DESTINATION
# =========================================================

def check_destination(city):
    """
    Get destination information and nearby
    geographic features.
    """

    location = find_location(city)

    if "error" in location:

        return location

    city_name = location.get(
        "name",
        city
    )

    country = location.get(
        "country",
        "Unknown"
    )

    country_code = location.get(
        "country_code",
        "Unknown"
    )

    latitude = location.get(
        "latitude"
    )

    longitude = location.get(
        "longitude"
    )

    elevation = location.get(
        "elevation"
    )

    timezone = location.get(
        "timezone",
        "Unknown"
    )

    population = location.get(
        "population"
    )

    feature_code = location.get(
        "feature_code",
        "Unknown"
    )

    admin1 = location.get(
        "admin1",
        "Unknown"
    )

    # -----------------------------------------------------
    # OPENSTREETMAP / OVERPASS
    # -----------------------------------------------------

    overpass_url = (
        "https://overpass-api.de/api/interpreter"
    )

    overpass_query = f"""
    [out:json][timeout:50];

    (
        nwr["natural"="beach"]
        (around:30000,{latitude},{longitude});

        nwr["natural"="peak"]
        (around:30000,{latitude},{longitude});

        nwr["natural"="mountain_range"]
        (around:30000,{latitude},{longitude});

        nwr["natural"="desert"]
        (around:30000,{latitude},{longitude});

        nwr["natural"="forest"]
        (around:30000,{latitude},{longitude});

        nwr["natural"="water"]
        (around:30000,{latitude},{longitude});

        nwr["route"="hiking"]
        (around:30000,{latitude},{longitude});
    );

    out tags;
    """

    headers = {
        "User-Agent":
            "SmartPack/1.0 "
            "(travel packing assistant)",
        "Referer":
            "http://127.0.0.1:8000/"
    }

    try:

        response = requests.post(
            overpass_url,
            data={
                "data": overpass_query
            },
            headers=headers,
            timeout=60
        )

        response.raise_for_status()

        feature_data = response.json()

    except requests.RequestException as e:

        print("\nOpenStreetMap error:")
        print(e)

        return {

            "city": city_name,

            "country": country,

            "country_code": country_code,

            "latitude": latitude,

            "longitude": longitude,

            "elevation": elevation,

            "timezone": timezone,

            "population": population,

            "feature_code": feature_code,

            "admin1": admin1,

            "type": "Unknown",

            "beach": "unknown",

            "mountains": "unknown",

            "desert": "unknown",

            "forest": "unknown",

            "water": "unknown",

            "hiking": "unknown"
        }

    # -----------------------------------------------------
    # ANALYZE FEATURES
    # -----------------------------------------------------

    features = feature_data.get(
        "elements",
        []
    )

    beach = False

    mountains = False

    desert = False

    forest = False

    water = False

    hiking = False

    for feature in features:

        tags = feature.get(
            "tags",
            {}
        )

        natural_type = tags.get(
            "natural"
        )

        route_type = tags.get(
            "route"
        )

        if natural_type == "beach":

            beach = True

        if natural_type in [
            "peak",
            "mountain_range"
        ]:

            mountains = True

        if natural_type == "desert":

            desert = True

        if natural_type == "forest":

            forest = True

        if natural_type == "water":

            water = True

        if route_type == "hiking":

            hiking = True

    # -----------------------------------------------------
    # DETERMINE DESTINATION TYPE
    # -----------------------------------------------------

    if beach:

        destination_type = (
            "Coastal / beach destination"
        )

    elif mountains:

        destination_type = (
            "Mountain / outdoor destination"
        )

    elif desert:

        destination_type = (
            "Desert destination"
        )

    elif forest:

        destination_type = (
            "Nature destination"
        )

    elif water:

        destination_type = (
            "Water / nature destination"
        )

    else:

        destination_type = (
            "Urban / inland destination"
        )

    # -----------------------------------------------------
    # RETURN DESTINATION PROFILE
    # -----------------------------------------------------

    return {

        "city": city_name,

        "country": country,

        "country_code": country_code,

        "latitude": latitude,

        "longitude": longitude,

        "elevation": elevation,

        "timezone": timezone,

        "population": population,

        "feature_code": feature_code,

        "admin1": admin1,

        "type": destination_type,

        "beach": beach,

        "mountains": mountains,

        "desert": desert,

        "forest": forest,

        "water": water,

        "hiking": hiking
    }


# =========================================================
# TOOL 3: ADD ITEM
# =========================================================

def add_item(item, packing_list):
    """
    Add an item to the packing list.
    """

    packing_list.append(item)

    return {

        "item_added": item,

        "packing_list": packing_list
    }


# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    print("\n====================================")
    print("TESTING WEATHER TOOL")
    print("====================================")

    weather = check_weather(
        "Delhi, India"
    )

    print(weather)


    print("\n====================================")
    print("TESTING DESTINATION TOOL")
    print("====================================")

    destination = check_destination(
        "Goa, India"
    )

    print(destination)


    print("\n====================================")
    print("TESTING ADD ITEM TOOL")
    print("====================================")

    packing_list = []

    print(
        add_item(
            "umbrella",
            packing_list
        )
    )

    print(
        add_item(
            "jacket",
            packing_list
        )
    )