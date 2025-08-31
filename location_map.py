import folium
import webbrowser
import os
import sys
import geocoder
import requests

def get_device_location():
    """
    Gets the approximate location of the device using IP address geolocation.

    Returns:
        tuple: (latitude, longitude) or (None, None) if failed.
    """
    print("Attempting to find your location based on your IP address...")
    try:
        response = requests.get("http://ip-api.com/json/")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                lat, lon = data["lat"], data["lon"]
                city, country = data.get("city", ""), data.get("country", "")
                print(f"Location found: {city}, {country}")
                return lat, lon
            else:
                print("Could not determine location from IP address.")
        else:
            print("Error contacting IP location service.")
    except Exception as e:
        print(f"An error occurred while trying to get your location: {e}")
        print("Please ensure you have an active internet connection for the lookup.")

    return None, None

def get_location_from_user():
    """
    Prompts the user to enter their latitude and longitude.
    Includes basic validation to ensure the input is a valid number.
    """
    while True:
        try:
            lat_str = input("Enter your latitude (e.g., 12.9716): ")
            if not lat_str:
                print("Using default latitude for Bengaluru: 12.9716")
                lat = 12.9716
            else:
                lat = float(lat_str)

            lon_str = input("Enter your longitude (e.g., 77.5946): ")
            if not lon_str:
                print("Using default longitude for Bengaluru: 77.5946")
                lon = 77.5946
            else:
                lon = float(lon_str)

            # Basic validation for coordinates
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            else:
                print("Invalid range. Latitude must be between -90 and 90, and Longitude between -180 and 180.")
        except ValueError:
            print("Invalid input. Please enter valid numbers for coordinates.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting program.")
            sys.exit()


def create_offline_map(lat, lon):
    """
    Creates a self-contained HTML map file using Folium.

    This function requires an internet connection to run, as it needs to
    download the map tiles from OpenStreetMap. However, the resulting
    HTML file is completely offline.

    Args:
        lat (float): The latitude of the location to mark.
        lon (float): The longitude of the location to mark.
    """
    # Create a map object centered at the user's location with a high zoom level
    # The tiles are fetched from OpenStreetMap by default
    print("\nGenerating map centered at ({}, {})...".format(lat, lon))
    m = folium.Map(location=[lat, lon], zoom_start=16)

    # Add a marker for the user's location with a popup
    folium.Marker(
        location=[lat, lon],
        popup="Your Location",
        tooltip="Click me!",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    # Add a circle to make the location more prominent
    folium.Circle(
        location=[lat, lon],
        radius=100,
        color="blue",
        fill=True,
        fill_color="lightblue",
    ).add_to(m)


    # Save the map to an HTML file
    map_filename = "offline_location_map.html"
    m.save(map_filename)
    print(f"Successfully created '{map_filename}'.")
    print("This file can be opened in any web browser without an internet connection.")

    return map_filename


def open_map_in_browser(filename):
    """
    Opens the specified HTML file in the default web browser.
    """
    try:
        # Construct a file:// URL for the absolute path of the file
        filepath = os.path.realpath(filename)
        webbrowser.open(f"file://{filepath}")
        print(f"Opening '{filename}' in your default browser.")
    except Exception as e:
        print(f"Could not open the file in a browser: {e}")
        print(f"Please open '{filename}' manually.")




if __name__ == "__main__":
    print("--- Automatic Offline Map Generator ---")
    print("This script will attempt to find your location automatically, then")
    print("generate an HTML file that shows it on a map, viewable offline.")
    print("Note: An internet connection is needed for the initial location lookup and map generation.")
    print("-" * 40)

    location = get_device_location()

    if location and all(location):
        latitude, longitude = location
        print(f"Using coordinates: Latitude={latitude}, Longitude={longitude}")
        map_file = create_offline_map(latitude, longitude)
        open_map_in_browser(map_file)
    else:
        print("\nCould not generate the map because the location could not be determined.")
        print("Exiting program.")
        sys.exit()