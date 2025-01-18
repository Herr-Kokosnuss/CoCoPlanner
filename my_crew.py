from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import os
from dotenv import load_dotenv
from flight import get_amadeus_client
from datetime import datetime
from utils import show_progress

# Load environment variables
load_dotenv()

class FlightOption(BaseModel):
    type: str = Field(..., description="The type of flight option (fastest or cheapest)")
    price: float = Field(..., description="The total price of all flights")
    travel_class: str = Field(..., description="The travel class (economy, business, first)")
    segments: List[Dict] = Field(..., description="List of all flight segments")
    total_duration: int = Field(..., description="Total duration in minutes including connections")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if hasattr(v, 'isoformat') else str(v)
        }
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs):
        # Convert to dict and ensure all values are JSON serializable
        d = super().dict(*args, **kwargs)
        return d

class Activity(BaseModel):
    name: str = Field(..., description="The name of the activity")
    description: str = Field(..., description="The description of the activity")
    location: str = Field(..., description="The location of the activity")
    date: str = Field(..., description="The date of the activity")
    cuisine: str = Field(..., description="The cuisine of the activity")
    why_its_suitable: str = Field(..., description="Why it's suitable for the user")
    rating: str = Field(..., description="The rating of the activity")
    reviews: str = Field(..., description="The reviews of the activity")

class DayPlan(BaseModel):
    date: str = Field(..., description="The date of the day plan")
    activities: List[Activity] = Field(..., description="The activities of the day plan")
    restaurants: List[str] = Field(..., description="The restaurants of the day plan")
    flight: Optional[FlightOption] = Field(None, description="The flight information")

class Itinerary(BaseModel):
    days: List[DayPlan] = Field(..., description="The day plans of the itinerary")
    name: str = Field(..., description="The name of the itinerary")
    hotel: str = Field(..., description="The hotel of the itinerary")
    flight_options: List[FlightOption] = Field(..., description="All flight options (2 cheapest and 2 fastest)")

@CrewBase
class SurpriseTravelCrew():
    """Surprise Travel Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def flight_search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['flight_search_agent'],
            tools=[],
            verbose=False,
            allow_delegation=False,
        )

    @agent
    def personalized_activity_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['personalized_activity_planner'],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            verbose=False,
            allow_delegation=False,
        )
                                    
    @agent
    def restaurant_scout(self) -> Agent:
        return Agent(
            config=self.agents_config['restaurant_scout'],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            verbose=False,
            allow_delegation=False,
        )
        
    @agent
    def itinerary_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_compiler'],
            tools=[],
            verbose=False,
            allow_delegation=False,
        )
        
    @task
    def flight_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['flight_search_task'],
            agent=self.flight_search_agent(),
        )

    @task
    def personalized_activity_planning_task(self) -> Task:
        """
        Plan activities considering the stay duration at each destination.
        For multi-city trips, activities should be planned according to the time spent at each stop.
        """
        return Task(
            config=self.tasks_config['personalized_activity_planning_task'],
            agent=self.personalized_activity_planner(),
        )
    
    @task
    def restaurant_scouting_task(self) -> Task:
        return Task(
            config=self.tasks_config['restaurant_scouting_task'],
            agent=self.restaurant_scout(),
        )
   
    @task
    def itinerary_compilation_task(self) -> Task:
        """
        Compile the itinerary ensuring activities fit within the specified stay duration.
        """
        return Task(
            config=self.tasks_config['itinerary_compilation_task'],
            agent=self.itinerary_compiler(),
        )
        
    @crew 
    def crew(self) -> Crew:
        """Creates a SurpriseTravel Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

    def get_flight_options(self, inputs):
        # Check if we have flight routes directly provided
        if 'flight_routes' in inputs:
            flight_options = search_flights(
                flight_routes=inputs['flight_routes'],
                travel_class=inputs['travel_class'],
                adults=inputs['adults'],
                children=inputs['children'],
                infants=inputs['infants'],
                non_stop=inputs.get('non_stop', False)
            )
        else:
            # Handle legacy format where origin/destination are provided directly
            flight_routes = [{
                "origin": inputs.get('origin'),
                "destination": inputs.get('destination'),
                "departure_date": inputs.get('departure_date')
            }]
            
            if inputs.get('return_date'):
                flight_routes.append({
                    "origin": inputs['destination'],
                    "destination": inputs['origin'],
                    "departure_date": inputs['return_date']
                })
                
            flight_options = search_flights(
                flight_routes=flight_routes,
                travel_class=inputs['travel_class'],
                adults=inputs['adults'],
                children=inputs['children'],
                infants=inputs['infants'],
                non_stop=inputs.get('non_stop', False)
            )
            
        return flight_options

    def kickoff(self, inputs):
        """Execute the crew with progress indicators"""
        # Flight Search Progress
        progress = show_progress("Searching for flights")
        try:
            flight_results = self.flight_search_task().execute(inputs)
        finally:
            progress.set()
            print("Flight search successful.")

        # Activity Planning Progress
        progress = show_progress("Planning activities")
        try:
            activity_results = self.personalized_activity_planning_task().execute(inputs)
        finally:
            progress.set()
            print("\n🎯  Activities planned!")

        # Restaurant Scouting Progress
        progress = show_progress("Finding restaurants")
        try:
            restaurant_results = self.restaurant_scouting_task().execute(inputs)
        finally:
            progress.set()
            print("\n🍽️  Restaurant recommendations ready!")

        # Itinerary Compilation Progress
        progress = show_progress("Creating your perfect itinerary")
        try:
            final_results = self.itinerary_compilation_task().execute(inputs)
        finally:
            progress.set()
            print("\n🌴  Your travel plan is ready!\n")

        return final_results

def search_flights(flight_routes, travel_class='economy', adults=1, children=0, infants=0, non_stop=False):
    """
    Search flights using Amadeus API
    Args:
        flight_routes (List[Dict]): List of routes, each containing origin, destination, and departure_date
        travel_class (str): economy, business, or first
        adults (int): Number of adult travelers (12+ years)
        children (int): Number of child travelers (2-11 years)
        infants (int): Number of infant travelers (0-2 years)
        non_stop (bool): If True, only search for non-stop flights
    """
    amadeus = get_amadeus_client()
    if not amadeus:
        return []

    try:
        # Map travel class to Amadeus format
        class_mapping = {
            'economy': 'ECONOMY',
            'business': 'BUSINESS',
            'first': 'FIRST'
        }
        
        # Search flights using the API client
        response = amadeus.search_flights(
            flight_routes=flight_routes,
            travel_class=class_mapping.get(travel_class.lower(), 'ECONOMY'),
            adults=adults,
            children=children,
            infants=infants,
            non_stop=non_stop
        )
        
        if not response or 'data' not in response:
            return []
            
        flight_options = []
        for offer in response['data']:
            segments = []
            total_duration = 0
            
            # Process all segments from all itineraries
            for itinerary in offer['itineraries']:
                for segment in itinerary['segments']:
                    segments.append({
                        'origin': segment['departure']['iataCode'],
                        'destination': segment['arrival']['iataCode'],
                        'departure_time': segment['departure']['at'],
                        'arrival_time': segment['arrival']['at'],
                        'duration': segment['duration'],
                        'carrier': segment['carrierCode'],
                        'flight_number': f"{segment['carrierCode']}{segment['number']}"
                    })
                    
            flight_option = FlightOption(
                type="cheapest" if offer in response['data'][:2] else "fastest",
                price=float(offer['price']['total']),
                travel_class=travel_class,
                segments=segments,
                total_duration=amadeus.get_total_duration(offer)
            )
            
            flight_options.append(flight_option)
            
        return flight_options

    except Exception as error:
        print(f"Error searching flights: {error}")
        return []
