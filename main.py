import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic._internal._config')
from my_crew import SurpriseTravelCrew
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from send_email import send_email
import ast
import random
from database import connect_to_mongodb, store_customer_data, update_results
from flight import get_amadeus_client
from airport_lookup import AirportLookup
from utils import (
    show_progress, 
    clear_screen, 
    print_centered,
    get_single_key
)
import time

# Load environment variables
load_dotenv()

def generate_search_id():
    """
    Generate a unique search ID.
    Format: 00XXXX for first 9999 entries, then 0XXXXX for next 90,000 entries
    """
    def create_id(prefix, digits):
        return f"{prefix}{random.randint(0, 10**digits - 1):0{digits}d}"
    
    # Connect to cloud database only
    collection = connect_to_mongodb()
    if collection is None:
        raise Exception("Could not connect to database")
    
    # Get count of existing entries
    total_entries = collection.count_documents({})

    # Determine format based on total entries
    if total_entries < 9999:
        prefix = "00"
        digits = 4
    else:
        prefix = "0"
        digits = 5

    max_attempts = 100  # Prevent infinite loop
    for _ in range(max_attempts):
        search_id = create_id(prefix, digits)
        
        # Check if ID exists in database
        if collection.find_one({"search_id": search_id}) is None:
            return search_id
            
    raise Exception(f"Could not generate unique search ID after {max_attempts} attempts")

def validate_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None

def validate_email(email):
    while not email.strip() or '@' not in email or '.' not in email:
        if not email.strip():
            print("Email cannot be empty. Please enter your email address.")
        else:
            print("Invalid email format. Please enter a valid email address.")
        email = input("Please enter your email address: ")
    return email.strip()

def get_non_empty_input(prompt, error_message="This field cannot be empty. Please try again."):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(error_message)

def get_airport_code(prompt):
    """Get airport code using the lookup system"""
    airport_lookup = AirportLookup()
    return airport_lookup.get_airport_selection(prompt)

def get_traveler_counts():
    """Get the number of travelers in each age group according to Amadeus standards"""
    while True:
        try:
            adults = int(input("How many adults (12+ years) are traveling?: ").strip())
            if adults < 1:
                print("Error: At least one adult traveler is required.")
                print("Children and infants must be accompanied by an adult.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    # Only ask for children/infants if there's at least one adult
    children = 0
    infants = 0
    
    while True:
        try:
            children = int(input("How many children (2-11 years) are traveling?: ").strip())
            if children < 0:
                print("Please enter a valid number (0 or more).")
                continue
            if children > 0 and adults == 0:
                print("Error: Children must be accompanied by at least one adult.")
                print("Please add adult travelers first.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            infants = int(input("How many infants (0-2 years) are traveling?: ").strip())
            if infants < 0:
                print("Please enter a valid number (0 or more).")
                continue
            if infants > adults:
                print("Error: Number of infants cannot exceed number of adults.")
                print("Each infant must be accompanied by an adult.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
            
    # Final validation of total travelers
    if adults == 0 and (children > 0 or infants > 0):
        print("Error: At least one adult traveler is required when traveling with children or infants.")
        return get_traveler_counts()  # Recursively ask again
            
    return adults, children, infants

def get_traveler_names(adults, children, infants):
    """Get names for all travelers"""
    travelers = []
    
    # Get adult names (12+ years)
    for i in range(adults):
        while True:
            name = input(f"Enter name for Adult {i+1} (12+ years): ").strip()
            if name:
                travelers.append({"type": "ADT", "name": name})
                break
            print("Name cannot be empty.")
    
    # Get children names (2-11 years)
    for i in range(children):
        while True:
            name = input(f"Enter name for Child {i+1} (2-11 years): ").strip()
            if name:
                travelers.append({"type": "CHD", "name": name})
                break
            print("Name cannot be empty.")
    
    # Get infant names (0-2 years)
    for i in range(infants):
        while True:
            name = input(f"Enter name for Infant {i+1} (0-2 years): ").strip()
            if name:
                travelers.append({"type": "INF", "name": name})
                break
            print("Name cannot be empty.")
            
    return travelers

def get_validated_date(prompt):
    """Get and validate a date in YYYY-MM-DD format"""
    while True:
        date_string = get_non_empty_input(prompt, "Date cannot be empty. Please enter a date.")
        validated_date = validate_date(date_string)
        if validated_date:
            # Check if date is not in the past
            try:
                input_date = datetime.strptime(validated_date, "%Y-%m-%d")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if input_date < today:
                    print("Error: Date cannot be in the past.")
                    continue
                return validated_date
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
        else:
            print("Invalid date format. Please use YYYY-MM-DD.")

def calculate_stay_duration(departure_date, return_date):
    """Calculate stay duration from dates"""
    d1 = datetime.strptime(departure_date, "%Y-%m-%d")
    d2 = datetime.strptime(return_date, "%Y-%m-%d")
    return (d2 - d1).days

def get_flight_route_info(trip_type):
    """Get flight route information based on trip type"""
    airport_lookup = AirportLookup()
    departure_info = []
    flight_routes = []
    stay_durations = []
    
    if trip_type == 'one-way':
        # Get departure airport
        origin_info = airport_lookup.get_airport_selection("Where would you like to start your journey from?")
        if not origin_info:
            return None
            
        departure_info.append(f"Departure location: {origin_info['full_name']}")
        
        # Get departure date
        departure_date = get_validated_date("\nEnter departure date (YYYY-MM-DD): ")
        departure_info.append(f"Departure date: {departure_date}")
        
        # Get destination airport
        dest_info = airport_lookup.get_airport_selection("Where would you like to fly to?", departure_info)
        if not dest_info:
            return None
            
        # Get stay duration for destination
        stay_duration = get_stay_duration(dest_info['city'])
        stay_durations.append(stay_duration)
        
        # Create flight route with stay duration
        flight_routes = [{
            "origin": origin_info['code'],
            "destination": dest_info['code'],
            "departure_date": departure_date,
            "origin_details": origin_info,
            "destination_details": dest_info,
            "stay_duration": stay_duration
        }]
        
    elif trip_type == 'round-trip':
        # Similar to one-way but add return flight
        origin_info = airport_lookup.get_airport_selection("Where would you like to start your journey from?")
        if not origin_info:
            return None
            
        departure_info.append(f"Departure location: {origin_info['full_name']}")
        
        departure_date = get_validated_date("\nEnter departure date (YYYY-MM-DD): ")
        departure_info.append(f"Departure date: {departure_date}")
        
        dest_info = airport_lookup.get_airport_selection("Where would you like to fly to?", departure_info)
        if not dest_info:
            return None
            
        departure_info.append(f"\nReturn from: {dest_info['full_name']}")
        return_date = get_validated_date("\nEnter return date (YYYY-MM-DD): ")
        
        # Calculate stay duration from dates
        stay_duration = calculate_stay_duration(departure_date, return_date)
        stay_durations.append(stay_duration)
        
        flight_routes = [
            {
                "origin": origin_info['code'],
                "destination": dest_info['code'],
                "departure_date": departure_date,
                "origin_details": origin_info,
                "destination_details": dest_info,
                "stay_duration": stay_duration
            },
            {
                "origin": dest_info['code'],
                "destination": origin_info['code'],
                "departure_date": return_date,
                "origin_details": dest_info,
                "destination_details": origin_info
            }
        ]
        
    elif trip_type == 'multi-city':
        # Handle multi-city route
        num_stops = get_num_stops()
        
        for i in range(num_stops):
            clear_screen()
            print_centered(f"Stop {i+1} of {num_stops}")
            print("\n")
            
            # Display previous route information
            for info in departure_info:
                print(info)
            print("\n")
            
            if i == 0:
                origin_info = airport_lookup.get_airport_selection("Where would you like to start your journey from?", departure_info)
                if not origin_info:
                    return None
            else:
                origin_info = flight_routes[-1]['destination_details']
                print(f"Departing from: {origin_info['full_name']}")
                
            departure_date = get_validated_date(f"\nEnter departure date for stop {i+1} (YYYY-MM-DD): ")
            
            departure_info.append(f"\nStop {i+1}:")
            departure_info.append(f"From: {origin_info['full_name']}")
            departure_info.append(f"Date: {departure_date}")
            
            dest_info = airport_lookup.get_airport_selection(f"Where would you like to fly to for stop {i+1}?", departure_info)
            if not dest_info:
                return None

            # Add the route first without stay duration
            flight_routes.append({
                "origin": origin_info['code'],
                "destination": dest_info['code'],
                "departure_date": departure_date,
                "origin_details": origin_info,
                "destination_details": dest_info
            })
            
            departure_info.append(f"To: {dest_info['full_name']}")

        # Calculate stay durations between stops
        for i in range(len(flight_routes) - 1):
            current_date = flight_routes[i]['departure_date']
            next_date = flight_routes[i + 1]['departure_date']
            stay_duration = calculate_stay_duration(current_date, next_date)
            flight_routes[i]['stay_duration'] = stay_duration
            stay_durations.append(stay_duration)
    
        # Check if final destination is different from start
        if flight_routes[-1]['destination'] != flight_routes[0]['origin']:
            print(f"\nWould you like to get a plan for your stay in {flight_routes[-1]['destination_details']['city']}?")
            print("y - Yes")
            print("n - No")
            
            if get_single_key().lower() == 'y':
                final_stay = get_stay_duration(flight_routes[-1]['destination_details']['city'])
                flight_routes[-1]['stay_duration'] = final_stay
                stay_durations.append(final_stay)
        else:
            # If returning to start, use the time between last flight and first flight
            stay_duration = calculate_stay_duration(flight_routes[-1]['departure_date'], flight_routes[0]['departure_date'])
            flight_routes[-1]['stay_duration'] = stay_duration
            stay_durations.append(stay_duration)
    
    # Update crew_inputs to include stay duration
    crew_inputs = {
        'stay_duration': stay_durations[0] if stay_durations else None,  # Use first duration for one-way/round-trip
        'stay_durations': stay_durations  # Full list for multi-city
    }
    
    return flight_routes

def format_trip_info(trip_info, hotel_locations=None):
    """Format trip information for display"""
    info = []
    info.append("Passenger Information:")
    info.append(f"Adults: {trip_info['adults']}")
    info.append(f"Children: {trip_info['children']}")
    info.append(f"Infants: {trip_info['infants']}")
    
    info.append("\nPassenger/s name/s:")
    for i, traveler in enumerate(trip_info['travelers'], 1):
        traveler_type = {
            'ADT': 'Adult',
            'CHD': 'Child',
            'INF': 'Infant'
        }[traveler['type']]
        info.append(f"{i}- {traveler['name']} ({traveler_type})")
    
    info.append(f"\nContact Email: {trip_info['email']}")
    
    info.append("\nFlight Information:")
    for i, route in enumerate(trip_info['flight_routes'], 1):
        if trip_info['trip_type'] == 'multi-city':
            info.append(f"\nFlight {i}:")
        info.append(f"From: {route['origin_details']['full_name']}")
        info.append(f"To: {route['destination_details']['full_name']}")
        info.append(f"Date: {route['departure_date']}")
        if 'stay_duration' in route:
            info.append(f"Stay Duration: {route['stay_duration']} days")

    if hotel_locations:
        info.append("\nHotel Information:")
        if trip_info['trip_type'] == 'multi-city':
            for i, hotel in enumerate(hotel_locations, 1):
                info.append(f"Stop {i} - Preferred hotel location in {hotel['city']}: {hotel['location']}")
        else:
            info.append(f"Preferred hotel location in {hotel_locations[0]['city']}: {hotel_locations[0]['location']}")
    
    return "\n".join(info)

def format_trip_info_with_numbers(trip_info, hotel_locations=None, travel_class=None, non_stop=None):
    """Format trip information with numbered items for modification"""
    info = []
    info.append("1. Passenger Information:")
    info.append(f"   Adults: {trip_info['adults']}")
    info.append(f"   Children: {trip_info['children']}")
    info.append(f"   Infants: {trip_info['infants']}")
    
    info.append("\n2. Passenger Names:")
    for i, traveler in enumerate(trip_info['travelers'], 1):
        traveler_type = {
            'ADT': 'Adult',
            'CHD': 'Child',
            'INF': 'Infant'
        }[traveler['type']]
        info.append(f"   {i}- {traveler['name']} ({traveler_type})")
    
    info.append(f"\n3. Contact Email: {trip_info['email']}")
    
    info.append("\n4. Flight Information:")
    for i, route in enumerate(trip_info['flight_routes'], 1):
        if trip_info['trip_type'] == 'multi-city':
            info.append(f"\n   Flight {i}:")
        info.append(f"   From: {route['origin_details']['full_name']}")
        info.append(f"   To: {route['destination_details']['full_name']}")
        info.append(f"   Date: {route['departure_date']}")
        if 'stay_duration' in route:
            info.append(f"   Stay Duration: {route['stay_duration']} days")

    if hotel_locations:
        info.append("\n5. Hotel Information:")
        if trip_info['trip_type'] == 'multi-city':
            for i, hotel in enumerate(hotel_locations, 1):
                info.append(f"   Stop {i} - Preferred location in {hotel['city']}: {hotel['location']}")
        else:
            info.append(f"   Preferred location in {hotel_locations[0]['city']}: {hotel_locations[0]['location']}")

    if travel_class is not None:
        info.append(f"\n6. Travel Class: {travel_class}")
        info.append(f"\n7. Non-stop Flights Only: {'Yes' if non_stop else 'No'}")
    
    return "\n".join(info)

def modify_trip_info(trip_info, hotel_locations, travel_class, non_stop):
    """Allow user to modify specific parts of the trip information"""
    while True:
        clear_screen()
        print_centered("Travel Plan Summary")
        print_centered("=====================")
        print("\n")
        print(format_trip_info_with_numbers(trip_info, hotel_locations, travel_class, non_stop))
        print("\n****************\n")
        print("What would you like to modify?")
        print("1 - Passenger counts")
        print("2 - Passenger names")
        print("3 - Email")
        print("4 - Flight information")
        print("5 - Hotel location")
        print("6 - Travel class")
        print("7 - Non-stop preference")
        print("\n\n")  # Double spacing
        print("8 - Confirm changes")
        print("q - Quit planning")

        choice = get_single_key().lower()
        
        if choice == '8':
            return trip_info, hotel_locations, travel_class, non_stop
        elif choice == 'q':
            return None, None, None, None
        
        # Handle modifications
        if choice in '1234567':
            clear_screen()
            if choice == '1':
                adults, children, infants = get_traveler_counts()
                travelers = get_traveler_names(adults, children, infants)
                trip_info.update({
                    'adults': adults,
                    'children': children,
                    'infants': infants,
                    'travelers': travelers
                })
            elif choice == '2':
                travelers = get_traveler_names(trip_info['adults'], trip_info['children'], trip_info['infants'])
                trip_info['travelers'] = travelers
            elif choice == '3':
                trip_info['email'] = validate_email(input("Please enter your email address: "))
            elif choice == '4':
                new_routes = get_flight_route_info(trip_info['trip_type'])
                if new_routes:
                    trip_info['flight_routes'] = new_routes
            elif choice == '5':
                hotel_locations = get_hotel_locations(trip_info)
            elif choice == '6':
                print("\nSelect travel class:")
                print("e - Economy")
                print("b - Business")
                print("f - First")
                while True:
                    travel_class = get_single_key().lower()
                    if travel_class in ['e', 'b', 'f']:
                        travel_class = {'e': 'economy', 'b': 'business', 'f': 'first'}[travel_class]
                        break
            elif choice == '7':
                print("\nDo you want non-stop flights only?")
                print("y - Yes")
                print("n - No")
                while True:
                    non_stop = get_single_key().lower()
                    if non_stop in ['y', 'n']:
                        non_stop = non_stop == 'y'
                        break

def get_hotel_locations(trip_info):
    """Get hotel locations with a list-style interface"""
    clear_screen()
    print_centered("Hotel Information")
    print_centered("================")
    print("\n")
    
    # Display trip information
    print(format_trip_info(trip_info))
    print("\n")

    hotel_locations = []
    if trip_info['trip_type'] == 'multi-city':
        print("Let's get hotel information for each stop:")
        for route in trip_info['flight_routes'][:-1]:
            print(f"\nAvailable areas in {route['destination_details']['city']}:")
            print("1. City Center")
            print("2. Airport Area")
            print("3. Custom Location")
            print("\nPress a key to select...")
            
            while True:
                choice = get_single_key()
                if choice == '1':
                    location = "City Center"
                    break
                elif choice == '2':
                    location = "Airport Area"
                    break
                elif choice == '3':
                    location = input("\nEnter custom location: ").strip()
                    if location:
                        break
                    print("Location cannot be empty. Please try again.")
            
            hotel_locations.append({
                "city": route['destination_details']['city'],
                "location": location
            })
            
            # Show updated information after each selection
            clear_screen()
            print_centered("Hotel Information")
            print_centered("================")
            print("\n")
            print(format_trip_info(trip_info, hotel_locations))
            print("\n")
    else:
        city = trip_info['flight_routes'][0]['destination_details']['city']
        print(f"\nAvailable areas in {city}:")
        print("1. City Center")
        print("2. Airport Area")
        print("3. Custom Location")
        print("\nPress a key to select...")
        
        while True:
            choice = get_single_key()
            if choice == '1':
                location = "City Center"
                break
            elif choice == '2':
                location = "Airport Area"
                break
            elif choice == '3':
                location = input("\nEnter custom location: ").strip()
                if location:
                    break
                print("Location cannot be empty. Please try again.")
        
        hotel_locations.append({
            "city": city,
            "location": location
        })

    return hotel_locations

def collect_trip_info():
    """Collect all trip information and return as a dictionary"""
    clear_screen()
    print_centered("Let's Plan Your Trip!")
    print("\n\n")  # Double spacing

    # Get traveler counts
    adults, children, infants = get_traveler_counts()
    print("\n")  # Add spacing
    
    # Get names for all travelers
    travelers = get_traveler_names(adults, children, infants)
    print("\n")  # Add spacing
    
    # Get email
    email = validate_email(input("Please enter your email address: "))
    print("\n")  # Add spacing
    
    # Get trip type
    print("Select trip type:")
    print("1. One-way")
    print("2. Round-trip")
    print("3. Multi-city")
    print("\nPress a key to select...")
    
    while True:
        trip_type_input = get_single_key()
        trip_type_mapping = {
            "1": "one-way",
            "2": "round-trip",
            "3": "multi-city"
        }
        
        if trip_type_input in trip_type_mapping:
            trip_type = trip_type_mapping[trip_type_input]
            break

    # Get flight route information
    flight_routes = get_flight_route_info(trip_type)
    if not flight_routes:
        return None

    return {
        'trip_type': trip_type,
        'adults': adults,
        'children': children,
        'infants': infants,
        'travelers': travelers,
        'email': email,
        'flight_routes': flight_routes
    }

def get_stay_duration(destination):
    """Get how many days the user plans to stay at their destination"""
    while True:
        try:
            days = int(input(f"\nHow many days would you like to explore {destination}? "))
            if days > 0:
                return days
            print("Please enter a number greater than 0.")
        except ValueError:
            print("Please enter a valid number.")

def get_num_stops():
    """Get number of stops for multi-city trip"""
    while True:
        try:
            print("\nHow many stops would you like to make?")
            print("(Minimum 2 stops - departure and final destination)")
            num_stops = int(input("Enter number of stops: "))
            if num_stops >= 2:
                return num_stops
            print("Please enter at least 2 stops.")
        except ValueError:
            print("Please enter a valid number.")

def run_crew():
    # Connect to cloud database only
    collection = connect_to_mongodb()
    if collection is None:
        print("Error: Could not connect to database")
        return

    # Generate search ID
    search_id = generate_search_id()

    # Collect trip information
    trip_info = collect_trip_info()
    if not trip_info:
        print_centered("Trip planning cancelled.")
        time.sleep(2)
        return

    # Get hotel locations
    hotel_locations = get_hotel_locations(trip_info)

    # Get travel preferences
    clear_screen()
    print_centered("Travel Preferences")
    print_centered("=================")
    print("\n")
    
    # Get travel class
    print("Select travel class:")
    print("e - Economy")
    print("b - Business")
    print("f - First")
    print("\nPress a key to select...")
    
    while True:
        travel_class = get_single_key().lower()
        if travel_class in ['e', 'b', 'f']:
            travel_class = {'e': 'economy', 'b': 'business', 'f': 'first'}[travel_class]
            break

    # Get non-stop preference
    print("\nDo you want non-stop flights only?")
    print("y - Yes")
    print("n - No")
    print("\nPress a key to select...")
    
    while True:
        non_stop_choice = get_single_key().lower()
        if non_stop_choice in ['y', 'n']:
            non_stop = non_stop_choice == 'y'
            break

    # Show final confirmation before proceeding
    while True:
        clear_screen()
        print_centered("Travel Plan Summary")
        print_centered("=====================")
        print("\n")
        print(format_trip_info_with_numbers(trip_info, hotel_locations, travel_class, non_stop))
        print("\n****************\n")
        print("Are the above information correct?")
        print("1 - Yes, start planning")
        print("2 - No, I need to make changes")
        print("q - Quit planning")
        print_centered("=====================\n")
        print("\n")
        choice = get_single_key().lower()
        if choice == '1':
            # Prepare crew inputs
            crew_inputs = {
                'trip_type': trip_info['trip_type'],
                'flight_routes': trip_info['flight_routes'],
                'travel_class': travel_class,
                'adults': trip_info['adults'],
                'children': trip_info['children'],
                'infants': trip_info['infants'],
                'non_stop': non_stop,
                'hotel_locations': hotel_locations,
                'travelers': trip_info['travelers'],
                'flight_options_text': "",
                'trip_details_text': format_trip_info(trip_info, hotel_locations),
                'stay_duration': trip_info['flight_routes'][0].get('stay_duration', 0)
            }

            # Start the actual planning process
            progress = show_progress("Searching for flights")
            try:
                crew = SurpriseTravelCrew()
                flight_options = crew.get_flight_options(crew_inputs)
            finally:
                progress.set()
                print("\n")

            if not flight_options:
                print_centered("No flight options found. Please try different dates or routes.")
                time.sleep(2)
                return

            # Format flight options text
            flight_options_text = ""
            flight_options_text += "\nCHEAPEST OPTIONS:\n"
            for i, option in enumerate(flight_options[:2], 1):
                flight_options_text += f"\nOption {i} - Cheapest:\n"
                flight_options_text += f"Total Price: €{option.price}\n"
                flight_options_text += f"Travel Class: {option.travel_class}\n"
                hours = option.total_duration // 60
                minutes = option.total_duration % 60
                flight_options_text += f"Total Duration: {hours}h {minutes}m\n\n"
                
                for j, segment in enumerate(option.segments, 1):
                    flight_options_text += f"Flight Segment {j}:\n"
                    flight_options_text += f"- From: {segment['origin']}\n"
                    flight_options_text += f"- To: {segment['destination']}\n"
                    flight_options_text += f"- Departure: {segment['departure_time']}\n"
                    flight_options_text += f"- Arrival: {segment['arrival_time']}\n"
                    flight_options_text += f"- Duration: {segment['duration']}\n"
                    flight_options_text += f"- Carrier: {segment['carrier']}\n"
                    flight_options_text += f"- Flight Number: {segment['flight_number']}\n\n"

            # Add fastest options
            flight_options_text += "\nFASTEST OPTIONS:\n"
            for i, option in enumerate(flight_options[2:4], 1):
                flight_options_text += f"\nOption {i} - Fastest:\n"
                flight_options_text += f"Total Price: €{option.price}\n"
                flight_options_text += f"Travel Class: {option.travel_class}\n"
                hours = option.total_duration // 60
                minutes = option.total_duration % 60
                flight_options_text += f"Total Duration: {hours}h {minutes}m\n\n"
                
                for j, segment in enumerate(option.segments, 1):
                    flight_options_text += f"Flight Segment {j}:\n"
                    flight_options_text += f"- From: {segment['origin']}\n"
                    flight_options_text += f"- To: {segment['destination']}\n"
                    flight_options_text += f"- Departure: {segment['departure_time']}\n"
                    flight_options_text += f"- Arrival: {segment['arrival_time']}\n"
                    flight_options_text += f"- Duration: {segment['duration']}\n"
                    flight_options_text += f"- Carrier: {segment['carrier']}\n"
                    flight_options_text += f"- Flight Number: {segment['flight_number']}\n\n"

            # Update crew inputs with flight options
            crew_inputs['flight_options_text'] = flight_options_text

            # Show itinerary planning progress
            progress = show_progress("Creating your perfect itinerary")
            try:
                results = crew.crew().kickoff(inputs=crew_inputs)
            finally:
                progress.set()
                print("\n")

            # Extract final result
            if hasattr(results, 'raw_output'):
                final_result = results.raw_output
            elif hasattr(results, 'output'):
                final_result = results.output
            elif hasattr(results, 'result'):
                final_result = results.result
            else:
                final_result = str(results)

            # Store in database
            customer_data = {
                "search_id": search_id,
                "timestamp": datetime.now(),
                "customer_info": {
                    "travelers": trip_info['travelers'],
                    "email": trip_info['email'],
                    "total_travelers": {
                        "adults": trip_info['adults'],
                        "children": trip_info['children'],
                        "infants": trip_info['infants']
                    }
                },
                "trip_details": {
                    "trip_type": trip_info['trip_type'],
                    "flight_routes": trip_info['flight_routes'],
                    "travel_class": travel_class,
                    "hotel_locations": hotel_locations
                },
                "flight_options": [flight.dict() for flight in flight_options],
                "flight_options_text": flight_options_text,
                "final_itinerary": final_result
            }

            if collection is not None:
                if not store_customer_data(customer_data, collection):
                    print("Warning: Failed to store initial data in database")
                update_results(datetime.now(), final_result, collection, search_id)

            # Display results
            clear_screen()

            print(final_result)
            print(f"\nYour search ID: {search_id}")

            # Ask about email notification
            while True:
                email_choice = input("\nDo you want to receive your itinerary by email? (Y/N): ").strip().lower()
                if email_choice in ['y', 'n']:
                    break
                print("Please enter Y or N")

            if email_choice == 'y':
                try:
                    # Get the customer name from travelers list
                    customer_name = trip_info['travelers'][0]['name']  # Use first traveler's name
                    
                    # Create a complete trip details dictionary
                    email_trip_details = {
                        **trip_info,  # Include all trip info
                        'travel_class': travel_class,  # Add travel class
                        'hotel_locations': hotel_locations  # Add hotel info
                    }
                    
                    send_email(
                        trip_info['email'],  # recipient email
                        customer_name,        # customer name
                        email_trip_details,   # complete trip details
                        final_result,        # results
                        search_id            # search ID
                    )
                except Exception as e:
                    print(f"\nFailed to send email: {str(e)}")

            break
        elif choice == '2':
            # Show modification menu
            trip_info, hotel_locations, travel_class, non_stop = modify_trip_info(
                trip_info, hotel_locations, travel_class, non_stop
            )
            if not trip_info:
                print_centered("Trip planning cancelled.")
                time.sleep(2)
                return
        elif choice == 'q':
            print_centered("Trip planning cancelled.")
            time.sleep(2)
            return

if __name__ == "__main__":
    run_crew()