from database import connect_to_mongodb
from datetime import datetime
import sys

def get_plan_by_search_id(search_id, collection):
    """Retrieve a travel plan using its search ID"""
    try:
        if collection is None:
            print("Error: No valid database connection")
            return None
            
        plan = collection.find_one({"search_id": search_id})
        if plan is not None:
            return plan
        
        print(f"\nNo plan found with search ID: {search_id}")
        return None
        
    except Exception as e:
        print(f"\nError retrieving plan: {str(e)}")
        return None

def format_flight_details(flight_option):
    """Format flight details for display"""
    details = []
    details.append(f"Type: {flight_option['type']}")
    details.append(f"Total Price: €{flight_option['price']}")
    details.append(f"Travel Class: {flight_option['travel_class']}")
    
    for i, flight in enumerate(flight_option['flights'], 1):
        details.append(f"\nFlight {i}:")
        details.append(f"  From: {flight['origin']}")
        details.append(f"  To: {flight['destination']}")
        details.append(f"  Departure: {flight['departure_time']}")
        details.append(f"  Arrival: {flight['arrival_time']}")
        details.append(f"  Duration: {flight['duration']}")
        
        if flight.get('transit_airports'):
            details.append("\n  Transit Points:")
            for transit in flight['transit_airports']:
                details.append(f"    Airport: {transit['airport']}")
                details.append(f"    Arrival: {transit['arrival_time']}")
                details.append(f"    Departure: {transit['departure_time']}")
    
    return "\n".join(details)

def display_plan(plan):
    """Display the travel plan in a readable format"""
    if not plan:
        return

    print("\n" + "="*50)
    print(f"Travel Plan - Search ID: {plan['search_id']}")
    print("="*50)
    
    print("\nTravelers Information:")
    print("-"*20)
    for traveler in plan['customer_info']['travelers']:
        traveler_type = {
            'ADT': 'Adult (12+ years)',
            'CHD': 'Child (2-11 years)',
            'INF': 'Infant (0-2 years)'
        }.get(traveler['type'], traveler['type'])
        print(f"{traveler_type}: {traveler['name']}")
    
    print(f"\nTotal Travelers:")
    print(f"Adults (12+ years): {plan['customer_info']['total_travelers']['adults']}")
    print(f"Children (2-11 years): {plan['customer_info']['total_travelers']['children']}")
    print(f"Infants (0-2 years): {plan['customer_info']['total_travelers']['infants']}")
    print(f"Contact Email: {plan['customer_info']['email']}")
    
    print("\nTrip Details:")
    print("-"*20)
    print(f"Trip Type: {plan['trip_details']['trip_type']}")
    print(f"Travel Class: {plan['trip_details']['travel_class']}")
    
    # Display flight routes
    print("\nFlight Routes:")
    for i, route in enumerate(plan['trip_details']['flight_routes'], 1):
        print(f"\nRoute {i}:")
        print(f"From: {route['origin']}")
        print(f"To: {route['destination']}")
        print(f"Date: {route['departure_date']}")
        
    print(f"\nCreated on: {plan['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'final_itinerary' in plan and plan['final_itinerary']:
        print("\nDetailed Itinerary:")
        print("-"*20)
        print(plan['final_itinerary'])

def main():
    # Connect to cloud database
    collection = connect_to_mongodb()
    if collection is None:
        print("Error: Could not connect to database")
        return

    while True:
        # Get search ID from user
        search_id = input("\nEnter the search ID (e.g., 001234) or 'q' to quit: ").strip()
        
        if search_id.lower() == 'q':
            print("\nGoodbye!")
            sys.exit(0)
        
        # Retrieve and display the plan
        plan = get_plan_by_search_id(search_id, collection)
        if plan:
            display_plan(plan)
        
        # Ask if user wants to search for another plan
        while True:
            another = input("\nWould you like to look up another plan? (y/n): ").strip().lower()
            if another in ['y', 'n']:
                break
            print("Please enter 'y' or 'n'")
        
        if another == 'n':
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main() 