import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

load_dotenv()

class AmadeusAPI:
    def __init__(self):
        # Initialize Amadeus client using credentials from .env
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
        )
        self.travel_class = None
        
    def search_flights(self, flight_routes, adults=1, children=0, infants=0, 
                      travel_class='ECONOMY', currency='EUR', max_results=20, non_stop=False):
        """Search for flight offers using the Amadeus SDK."""
        try:
            # Construct originDestinations list
            origin_destinations = []
            for i, route in enumerate(flight_routes):
                origin_destinations.append({
                    "id": str(i + 1),
                    "originLocationCode": route["origin"],
                    "destinationLocationCode": route["destination"],
                    "departureDateTimeRange": {
                        "date": route["departure_date"]
                    }
                })

            # Construct travelers list
            travelers = []
            # Add adults
            for i in range(adults):
                travelers.append({"id": str(i+1), "travelerType": "ADULT"})
            # Add children
            for i in range(children):
                travelers.append({"id": str(i+adults+1), "travelerType": "CHILD"})
            # Add infants
            for i in range(infants):
                travelers.append({"id": str(i+adults+children+1), "travelerType": "HELD_INFANT"})

            # Prepare search criteria with non-stop filter if requested
            search_criteria = {
                "maxFlightOffers": max_results,
                "flightFilters": {
                    "cabinRestrictions": [{
                        "cabin": travel_class,
                        "coverage": "ALL_SEGMENTS",
                        "originDestinationIds": [str(i+1) for i in range(len(flight_routes))]
                    }]
                }
            }

            # Add non-stop filter if requested
            if non_stop:
                search_criteria["flightFilters"]["connectionRestriction"] = {
                    "maxNumberOfConnections": 0
                }

            # Search flights using SDK
            response = self.amadeus.shopping.flight_offers_search.post(
                body={
                    "currencyCode": currency,
                    "originDestinations": origin_destinations,
                    "travelers": travelers,
                    "sources": ["GDS"],
                    "searchCriteria": search_criteria
                }
            )

            # Convert response to dictionary format
            if response and hasattr(response, 'data'):
                self.travel_class = travel_class
                return {
                    'data': self.sort_flights(response.data, travel_class)
                }
            else:
                return None

        except ResponseError as error:
            print(f"Error during flight search: {error}")
            return None
        except Exception as e:
            print(f"Error searching flights: {str(e)}")
            return None

    # Keep existing helper methods unchanged
    def parse_duration(self, duration_str):
        """Parse PT duration format to minutes"""
        duration = duration_str[2:]  # Remove 'PT'
        hours = 0
        minutes = 0
        
        if 'H' in duration:
            h_index = duration.index('H')
            hours = int(duration[:h_index])
            duration = duration[h_index + 1:]
        
        if 'M' in duration:
            m_index = duration.index('M')
            minutes = int(duration[:m_index])
        
        return hours * 60 + minutes

    def get_total_duration(self, flight):
        """Calculate total duration including all segments and connections"""
        total_minutes = 0
        
        # Process all itineraries (outbound and return)
        for itinerary in flight['itineraries']:
            # Add segment durations
            for segment in itinerary['segments']:
                total_minutes += self.parse_duration(segment['duration'])
            
            # Add connection times
            for i in range(len(itinerary['segments']) - 1):
                arrival = datetime.fromisoformat(itinerary['segments'][i]['arrival']['at'].replace('Z', '+00:00'))
                departure = datetime.fromisoformat(itinerary['segments'][i + 1]['departure']['at'].replace('Z', '+00:00'))
                connection_time = int((departure - arrival).total_seconds() / 60)
                total_minutes += connection_time
        
        return total_minutes

    def format_duration(self, minutes):
        """Convert minutes to hours and minutes format"""
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m"

    def sort_flights(self, flights, travel_class='ECONOMY'):
            """Sort flights by price and total duration"""
            # Store the travel class for filtering
            self.travel_class = travel_class
            
            # Filter flights by requested travel class
            filtered_flights = [f for f in flights if f['travelerPricings'][0]['fareDetailsBySegment'][0]['cabin'] == travel_class]
            if not filtered_flights:
                print(f"No flights found in {travel_class} class, showing all options")
                filtered_flights = flights
            
            # Sort by price
            price_sorted = sorted(filtered_flights, key=lambda x: float(x['price']['total']))
            
            # Sort by total duration
            duration_sorted = sorted(filtered_flights, key=lambda x: self.get_total_duration(x))
            
            # Get 2 cheapest options
            cheapest = price_sorted[:2]
            
            # Get 2 fastest options (allow overlap with cheapest)
            fastest = duration_sorted[:2]
            
            # Combine results, ensuring no duplicates
            sorted_flights = cheapest
            for flight in fastest:
                if flight not in sorted_flights:  # Avoid duplicates
                    sorted_flights.append(flight)
            
            return sorted_flights

def get_amadeus_client():
    """Create and return an authenticated Amadeus API client"""
    try:
        api = AmadeusAPI()
        return api
    except Exception as e:
        print(f"Error initializing Amadeus client: {str(e)}")
        return None 
    