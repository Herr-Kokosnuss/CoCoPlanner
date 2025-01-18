import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import ast

# Load environment variables
load_dotenv()

def format_results(results):
    """Convert results to a readable format"""
    # If it's a CrewOutput object, get the raw output
    if hasattr(results, 'raw_output'):
        return results.raw_output
    elif hasattr(results, 'output'):
        return results.output
    elif hasattr(results, 'result'):
        return results.result
    
    # If it's already a string, return it
    if isinstance(results, str):
        return results
        
    # If somehow we get a dict, convert it to string
    if isinstance(results, dict):
        return json.dumps(results, indent=2)
    
    # Fallback
    return str(results)

def format_trip_details(trip_details):
    """Format trip details for display in email"""
    details = []
    
    # Add trip type
    details.append(f"Trip Type: {trip_details.get('trip_type', 'Not specified')}")
    
    # Add flight routes
    if 'flight_routes' in trip_details:
        details.append("\nFlight Routes:")
        for i, route in enumerate(trip_details['flight_routes'], 1):
            details.append(f"\nRoute {i}:")
            details.append(f"From: {route['origin_details']['full_name']}")
            details.append(f"To: {route['destination_details']['full_name']}")
            details.append(f"Date: {route['departure_date']}")
            if 'stay_duration' in route:
                details.append(f"Stay Duration: {route['stay_duration']} days")
    
    # Add hotel information if available
    if 'hotel_locations' in trip_details:
        details.append("\nHotel Preferences:")
        for hotel in trip_details['hotel_locations']:
            details.append(f"Location in {hotel['city']}: {hotel['location']}")
    
    # Add travel class if available
    if 'travel_class' in trip_details:
        details.append(f"\nTravel Class: {trip_details['travel_class']}")
    
    return "\n".join(details)

def send_email(recipient_email, customer_name, trip_details, results, search_id):
    """Send email with trip details and results"""
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = f"Your Trip Search Results - ID: {search_id} - {datetime.now().strftime('%Y-%m-%d')}"

    # Format the trip details
    trip_details_text = format_trip_details(trip_details)

    # Format the results
    formatted_results = format_results(results)

    # Create the email body
    email_body = f"""
Dear {customer_name},

Thank you for using Cocoplanner travel service! Here are the details of your search:

Search ID: {search_id}

Trip Details:
-------------
{trip_details_text}


{formatted_results}

If you have any questions or feedback, please don't hesitate to contact us by replying to this email.

Best regards,
Your Travel Planning Team
    """

    message.attach(MIMEText(email_body, "plain"))

    try:
        # Create SMTP session
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"\nEmail sent successfully to {recipient_email}")
    except Exception as e:
        print(f"\nError sending email: {str(e)}") 