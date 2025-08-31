import pandas as pd
from geopy.geocoders import Nominatim
import time
import folium
import webbrowser
import os
import sys
import requests
from delhi_districts import delhi_districts


# --- Geocoding and Data Loading Functions ---

# Initialize the geolocator
geolocator = Nominatim(user_agent="crime_probability_mapper_v3")

def load_data(filepath):
    """
    Loads the crime dataset from a CSV file.
    """
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')
        print("Dataset loaded and columns standardized successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found. Please make sure it's in the same directory as the script.")
        return None
    except Exception as e:
        print(f"An error occurred while loading the data: {e}")
        return None

def get_district_from_coords(latitude, longitude):
    """
    Performs a reverse geocoding lookup to find the district (for non-Delhi locations).
    """
    try:
        time.sleep(1)
        location = geolocator.reverse((latitude, longitude), exactly_one=True, language='en')
        if location and 'address' in location.raw:
            address = location.raw['address']
            district = address.get('county', address.get('state_district', address.get('city_district')))
            if district:
                return district.replace(' District', '').strip()
            print("Could not determine district from coordinates' address details.")
            return None
        else:
            print("Could not find location details for the given coordinates.")
            return None
    except Exception as e:
        print(f"An error occurred during reverse geocoding: {e}")
        return None

def get_nearest_delhi_district(latitude, longitude):
    """
    Finds the nearest Delhi district from the dictionary based on squared Euclidean distance.
    """
    print("Calculating nearest Delhi district based on coordinates...")
    min_dist_sq = float('inf')
    nearest_district = None

    for district, coords in delhi_districts.items():
        # Calculate squared Euclidean distance (avoids costly square root)
        dist_sq = (latitude - coords[0])**2 + (longitude - coords[1])**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest_district = district
    
    return nearest_district

def get_crime_probability(df, district_name):
    """
    Searches for a district within Delhi in the DataFrame and returns its normalized crime score.
    """
    if district_name is None:
        return None
    
    # First, filter the DataFrame to only include rows where the state is Delhi.
    # The 'State/ UT' column was standardized to 'state__ut' during the initial data load.
    delhi_df = df[df['state__ut'].str.lower().str.contains('delhi', na=False)]
    
    # Now, search for the specific district within the filtered Delhi data.
    result = delhi_df[delhi_df['district__area'].str.lower() == district_name.lower()]
    
    if not result.empty:
        # Return the 'normalized_score' for the matching district.
        return result['normalized_score'].iloc[0]
    else:
        # Return None if the district is not found within the Delhi subset.
        return None

# --- Location Finding Functions ---

def get_device_location():
    """
    Gets the approximate location of the device using an IP address geolocation API.
    """
    print("Attempting to find your location based on your IP address...")
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                lat, lon = data.get("lat"), data.get("lon")
                city, country = data.get("city", "N/A"), data.get("country", "N/A")
                print(f"Location found: {city}, {country}")
                return lat, lon
            else:
                print("Could not determine location from IP address service.")
        else:
            print("Error contacting IP location service.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while trying to get your location: {e}")
        print("Please ensure you have an active internet connection for the lookup.")
    return None, None

def get_location_from_user():
    """
    Prompts the user to enter their latitude and longitude with validation.
    """
    while True:
        try:
            lat_str = input("Enter your latitude (e.g., 28.6139): ")
            lat = float(lat_str)
            lon_str = input("Enter your longitude (e.g., 77.2090): ")
            lon = float(lon_str)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            else:
                print("Invalid range. Latitude must be between -90 and 90, and Longitude between -180 and 180.")
        except ValueError:
            print("Invalid input. Please enter valid numbers for coordinates.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting program.")
            sys.exit()

# --- Map Generation Functions ---
def create_offline_map(lat, lon, district, probability):
    """
    Creates a self-contained HTML map file using Folium, including crime data.
    """
    print(f"\nGenerating map centered at ({lat:.4f}, {lon:.4f})...")
    m = folium.Map(location=[lat, lon], zoom_start=15)

    if district and probability is not None:
        popup_html = f"<b>Location:</b> {district}<br><b>Crime Probability:</b> {probability:.4f}<hr><i>Coordinates: ({lat:.4f}, {lon:.4f})</i>"
        icon_color = "red" if probability > 0.05 else "orange" if probability > 0.02 else "green"
    else:
        popup_html = f"<b>Location:</b> District Unknown<br><i>Crime data not available.</i><hr><b>Coordinates:</b> ({lat:.4f}, {lon:.4f})"
        icon_color = "gray"

    iframe = folium.IFrame(html=popup_html, width=250, height=100)
    popup = folium.Popup(iframe, max_width=250)

    folium.Marker(location=[lat, lon], popup=popup, tooltip="Click for details", icon=folium.Icon(color=icon_color, icon="info-sign")).add_to(m)
    folium.Circle(location=[lat, lon], radius=200, color=icon_color, fill=True, fill_color=icon_color, fill_opacity=0.2).add_to(m)

    map_filename = "crime_location_map.html"
    m.save(map_filename)
    print(f"Successfully created '{map_filename}'.")
    return map_filename

def open_map_in_browser(filename):
    """
    Opens the specified HTML file in the default web browser.
    """
    try:
        filepath = os.path.realpath(filename)
        webbrowser.open(f"file://{filepath}")
        print(f"Opening '{filename}' in your default browser.")
    except Exception as e:
        print(f"Could not open the file in a browser: {e}")
        print(f"Please open '{filename}' manually from your file explorer.")

# --- Main Execution Block ---

if __name__ == "__main__":
    print("--- Crime Probability Map Generator ---")
    print("-" * 40)

    csv_filepath = 'district_crime_scores.csv'
    crime_data_df = load_data(csv_filepath)
    if crime_data_df is None:
        sys.exit("Exiting: Could not load the required dataset.")

    latitude, longitude = get_device_location()
    if latitude is None or longitude is None:
        print("\nAutomatic location lookup failed.")
        if input("Enter location manually? (y/n): ").lower() == 'y':
            latitude, longitude = get_location_from_user()
        else:
            sys.exit("Exiting: Location not provided.")
    
    if latitude is None or longitude is None:
        sys.exit("Exiting program as location could not be determined.")

    district = None
    probability = None
    
    # Define a bounding box for Delhi to decide which method to use
    # DELHI_BOUNDS = {'lat_min': 28.4, 'lat_max': 28.9, 'lon_min': 76.8, 'lon_max': 77.4}

    # if (DELHI_BOUNDS['lat_min'] <= latitude <= DELHI_BOUNDS['lat_max'] and
    #     DELHI_BOUNDS['lon_min'] <= longitude <= DELHI_BOUNDS['lon_max']):
    #     print("\nLocation is within the Delhi-NCR region. Using nearest district calculation.")
    #     district = get_nearest_delhi_district(latitude, longitude)
    # else:
    #     print("\nLocation is outside Delhi. Using reverse geocoding.")
    #     district = get_district_from_coords(latitude, longitude)

    print("Printing the nearest location")
    district = get_nearest_delhi_district(latitude, longitude)
    print(district)

    print("\n--- Crime Probability Result ---")
    if district:
        print(f"Your estimated district is: {district}")
        probability = get_crime_probability(crime_data_df, district)
        if probability is not None:
            print(f"The crime probability for {district} is: {probability:.6f}")
        else:
            print(f"Crime data for '{district}' could not be found in the dataset.")
    else:
        print("Could not determine your district from the provided coordinates.")
    print("--------------------------------")

    map_file = create_offline_map(latitude, longitude, district, probability)
    open_map_in_browser(map_file)

