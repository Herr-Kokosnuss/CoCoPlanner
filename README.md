# CocoPLANER - AI-Powered Travel Planning Assistant

## Project Overview
CocoPLANER is an intelligent travel planning assistant that combines **traditional travel planning** with **modern AI technology**. Built with **Python** and powered by **CrewAI**, it provides personalized travel itineraries, real-time flight information, and comprehensive travel management through an interactive command-line interface.

---

## Key Features

### 1. Core Components
- **CLI Interface:** Beautiful ASCII art-based interface for user interaction  
- **AI Planning Engine:** Powered by CrewAI for intelligent travel recommendations  
- **Flight Integration:** Real-time flight data through Amadeus API  
- **Database System:** MongoDB for plan storage and retrieval  
- **Email System:** Automated notifications and updates  
- **Airport Database:** Comprehensive global airport information  

### 2. AI Integration
- **CrewAI Framework:** Powers the intelligent planning system  
- **OpenAI Integration:** Enhanced natural language processing  
- **Contextual Understanding:** Adapts to user preferences  
- **Smart Recommendations:** AI-driven travel suggestions  

### 3. Application Features
- **Travel Planning:** Intelligent itinerary creation  
- **Flight Search:** Real-time flight information and booking assistance  
- **Plan Management:** Save and retrieve travel plans  
- **Email Updates:** Automated travel notifications  
- **Airport Lookup:** Global airport database integration  

### 4. Technical Features
- **MongoDB Integration:** Robust data persistence  
- **API Integration:** Amadeus flight data system  
- **Docker Support:** Containerized deployment  
- **Email System:** SMTP-based notification system  

### 5. Automation
- **Automation System** through GitHub Actions and AWS  
  - Automated Docker builds and ECR pushes
  - Auto-scaling group management
  - Continuous deployment pipeline
---

## Technical Stack
- **Backend:** Python 3.8+  
- **AI Framework:** CrewAI  
- **Database:** MongoDB  
- **APIs:** Amadeus Flight API  
- **Container:** Docker  
- **Web Framework:** Flask  
- **Data Processing:** Pandas  

---

## Architecture
The application is built around a **command-line interface** that integrates with various services:
- **AI Planning System** powered by CrewAI  
- **Flight Data System** through Amadeus API  
- **Storage System** using MongoDB  
- **Notification System** via SMTP  
- **Airport Information System** using local database  

---

## System Components
1. **Interface Layer:** Command-line interface (`interface.py`)  
2. **Core Logic:** Main application engine (`main.py`)  
3. **Flight System:** Flight search and booking (`flight.py`)  
4. **Database Layer:** Data persistence (`database.py`)  
5. **AI System:** CrewAI configuration (`my_crew.py`)  
6. **Utility Layer:** Helper functions (`utils.py`)  
7. **Airport System:** Code lookup (`airport_lookup.py`)  
8. **Communication:** Email system (`send_email.py`)  
9. **Plan Management:** Retrieval system (`retrieve_plan.py`)  

---

## Security Considerations
- **API Key Management:** Secure handling of service credentials  
- **Database Security:** MongoDB security best practices  
- **Email Security:** Secure SMTP configuration  
- **Environment Variables:** Sensitive data protection  
- **Configuration Files:** Secure credential management  

---

## Dependencies and Requirements
- **Python Environment:** Python 3.8 or higher  
- **Database System:** MongoDB instance  
- **API Access:** Amadeus API credentials  
- **AI Services:** OpenAI API key  
- **Email Service:** SMTP server access  

---

## Important Notes
This repository contains the core application code for demonstration purposes. Configuration files and environment variables have been removed for security reasons. To run the application, please [proceed to CocoLancer](https://cocolancer.com).


---

*"Old-World Charm, Future-Driven Travel" - CocoPLANER*
