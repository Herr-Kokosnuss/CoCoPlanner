import pandas as pd
from utils import clear_screen, print_centered

class AirportLookup:
    def __init__(self, csv_path='airport_codes.csv'):
        """Initialize with airport data from CSV"""
        try:
            self.airports_df = pd.read_csv(csv_path)
            # Split Airport column into City and Airport name where applicable
            self.airports_df[['City', 'Airport_Name']] = self.airports_df['Airport'].str.split(',', n=1, expand=True)
            # Clean up the split results
            self.airports_df['City'] = self.airports_df['City'].str.strip()
            self.airports_df['Airport_Name'] = self.airports_df['Airport_Name'].fillna('').str.strip()
        except Exception as e:
            print(f"Error loading airport data: {str(e)}")
            self.airports_df = None

    def search_airports(self, query):
        """Search airports by code, city, airport name, or country"""
        if self.airports_df is None:
            return []
            
        query = query.lower().strip()
        
        # Search in all relevant columns
        matches = self.airports_df[
            self.airports_df['Code'].str.lower().str.contains(query) |
            self.airports_df['City'].str.lower().str.contains(query) |
            self.airports_df['Airport_Name'].str.lower().str.contains(query) |
            self.airports_df['Country'].str.lower().str.contains(query)
        ]
        
        return matches

    def get_airport_selection(self, prompt, departure_info=None):
        """Interactive airport selection process"""
        if self.airports_df is None:
            print("Airport data not available. Please enter IATA code directly.")
            return None
            
        while True:
            clear_screen()
            print_centered("Airport Selection")
            print_centered("================")
            print("\n")
            
            # Display departure info if provided
            if departure_info:
                for line in departure_info:
                    print(line)
                print("\n")
            
            search_term = input(f"{prompt}\nEnter city name, airport name, country, or IATA code (or 'q' to quit): ").strip()
            
            if search_term.lower() == 'q':
                return None
                
            if not search_term:
                print("Please enter a search term.")
                continue
                
            matches = self.search_airports(search_term)
            
            if len(matches) == 0:
                print("\nNo matching airports found. Press Enter to try again.")
                input()
                continue
                
            # Display matches with sequential numbering
            print("\nMatching airports:")
            for i, (_, row) in enumerate(matches.iterrows(), 1):
                airport_info = f"{row['City']}"
                if row['Airport_Name']:
                    airport_info += f" - {row['Airport_Name']}"
                print(f"{i}. {airport_info} ({row['Code']}) - {row['Country']}")
                
            # Get user selection
            while True:
                try:
                    selection = input("\nEnter the number of your chosen airport (or 0 to search again): ")
                    if selection == '0':
                        break
                        
                    selection = int(selection)
                    if 1 <= selection <= len(matches):
                        # Get the selected row using iloc with adjusted index
                        selected_row = matches.iloc[selection - 1]
                        selected_code = selected_row['Code']
                        selected_city = selected_row['City']
                        selected_airport = selected_row['Airport_Name']
                        selected_country = selected_row['Country']
                        
                        selected_text = f"{selected_city}"
                        if selected_airport:
                            selected_text += f" - {selected_airport}"
                        selected_text += f" ({selected_code}) - {selected_country}"
                        
                        print(f"\nSelected: {selected_text}")
                        
                        return {
                            'code': selected_code,
                            'city': selected_city,
                            'airport': selected_airport,
                            'country': selected_country,
                            'full_name': selected_text
                        }
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
