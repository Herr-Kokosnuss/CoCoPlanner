from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def serialize_flight_option(obj):
    """Custom JSON serializer for FlightOption objects"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    return str(obj)

def connect_to_mongodb():
    """
    Connect to MongoDB Atlas cloud database
    """
    try:
        # MongoDB Atlas connection
        mongodb_uri = os.getenv('MONGODB_ATLAS_URI')
        if not mongodb_uri:
            print("Error: MongoDB Atlas URI not found in environment variables")
            return None
        
        client = MongoClient(mongodb_uri)
        db = client['trip-cloud']
        return db['customer_entries']
            
    except Exception as e:
        print(f"Error: Failed to connect to cloud database: {str(e)}")
        return None

def store_customer_data(customer_data, collection):
    """Store customer data in MongoDB Atlas"""
    if collection is None:
        print("Error: No valid database connection")
        return False
        
    try:
        # Validate data structure
        if 'customer_info' not in customer_data:
            raise ValueError("Missing customer_info in data")
            
        if 'trip_details' in customer_data:
            if 'flight_routes' not in customer_data['trip_details']:
                raise ValueError("Missing flight routes in trip details")
                
            for route in customer_data['trip_details']['flight_routes']:
                if not all(k in route for k in ['origin', 'destination', 'departure_date']):
                    raise ValueError("Invalid flight route structure")
        
        # Convert FlightOption objects to dict for storage
        if 'flight_options' in customer_data:
            customer_data['flight_options'] = [
                flight.dict() if hasattr(flight, 'dict') else flight 
                for flight in customer_data['flight_options']
            ]
            
        # Store in cloud database
        result = collection.insert_one(customer_data)
        if result.inserted_id:
            print("Successfully stored in cloud database")
            return True
            
    except Exception as e:
        print(f"Error: Failed to store data in database: {str(e)}")
        
    return False

def update_results(timestamp, final_result, collection, search_id):
    """Update results in MongoDB Atlas"""
    if collection is None:
        print("Error: No valid database connection")
        return
        
    try:
        update_data = {
            "$set": {
                "final_itinerary": final_result,
                "last_updated": datetime.now()
            }
        }
        
        result = collection.update_one(
            {"search_id": search_id},
            update_data
        )
        if result.modified_count > 0:
            print("Successfully updated in cloud database")
            
    except Exception as e:
        print(f"Error: Failed to update results in database: {str(e)}")