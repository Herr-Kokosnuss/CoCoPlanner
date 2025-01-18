import sys
import time
from utils import (
    clear_screen, 
    print_centered, 
    show_progress,
    get_single_key
)
from retrieve_plan import get_plan_by_search_id, display_plan
from database import connect_to_mongodb
from main import run_crew

def display_logo():
    """Display the Cocolancer logo and welcome menu"""
    logo = """
                                                              **#%#*                                
                                                          ***#@#**                                  
                                                        ***#@****                                   
                                 **###*******         ##*#@#****                                    
                               %%#*****#%%#****      ####@***#                                      
                                     ******%@#***   ####@#**                                        
                                         ****%%*** @###%%##                                         
                                          ***##@#**@@#@@*#                                          
                                             ###%%##@@@%##  *********##                             
                                               ##%%#%@@%#####@%###***#%%@@                          
                                                @@@@@@@%#%@#*********                               
                                        #******* @@@@@@@@%####*##                                   
                                     ***#%@%%@@@%%@@@@@@@####                                       
                                 ***#%#**********#@@@@@%%%%#                                        
                                **@##******#**##*#@###%%@%##*#                                      
                              #*%%##*****    #**%#***#%##*#@%###                                    
                            ###%####**      #**@#****#@%#**=*#%##                                   
                           ##%%#####       #**@#+**##*@@@ *****@##                                  
                          %%@@%###         #*@###### %#%@@ #***#@##                                 
                          %%@%%%#          ##@#####   *#%@   ####@##                                
                          @@%%@           ##%#####    **%@@   ###%@%@                               
                          @@%%            ##@####      *#%@    #%@@@@                               
                          @@%             %%@%%##       *%@@     @@@@                               
                           @               %@%%%        *#%@       @@                               
                                           %@%%         **%@@       @                               
                                            @%          **%%@                                       
                                                         *#%@                                       
                                                         **%@@                                      
                                                         **%%@                                      
                                                         **%%@                                      
                                                         **%@@                                      
                                                         **%%@                                      
                                                         **%%@                                      
                                                         **%%@@                                     
                                                         @@@@@                                      
                                                         **%%@@                                     
                                                         **%%@@                                     
                                                         **%%@@                                     
                                                        ***%%@@                                     
                                                         **%%@@                                     
                                                         **#%@@                                     
                                                        ***#%@@                                     
                                                        *%%%%@@                                     
                                                         **%%@@                                     
                                                        ***%%@@                                     
                                                        **#%%@@                                     
                                                        **#%@@                                      
                                                        **#%@@#                                     
                                                        **#%@@*                                     
                                                       ***%%@@*                                     
                                                           %%@*   
    """

    header = """
              ============================================
                  C O C O P L A N E R
           "Old-World Charm, Future-Driven Travel"
              ============================================
    """

    welcome_text = """
    [1] Start Planning Your Journey
    [2] Retrieve Existing Plan
    [q] Quit
    
    Use the keys [1], [2], or [q] to make a selection...
    """

    clear_screen()
    print_centered(logo)
    print_centered(header)
    print_centered(welcome_text)

def main():
    while True:
        display_logo()
        choice = get_single_key().lower()
        
        if choice == 'q':
            clear_screen()
            print_centered("Thank you for using Cocolancer Travel Planner!")
            print_centered("Have a great journey! 🥥✈️")
            time.sleep(2)
            sys.exit(0)
            
        elif choice == '1':
            clear_screen()
            print_centered("Starting Your Travel Planning Journey...")
            time.sleep(1)
            run_crew()
            input("\nPress Enter to return to the main menu...")
            
        elif choice == '2':
            clear_screen()
            print_centered("Retrieve Your Travel Plan")
            print_centered("-----------------------")
            
            collection = connect_to_mongodb()
            if collection is None:
                print_centered("Error: Could not connect to the database")
                time.sleep(2)
                continue
                
            search_id = input("\nEnter your plan ID: ").strip()
            progress = show_progress("Retrieving your plan")
            try:
                plan = get_plan_by_search_id(search_id, collection)
                progress.set()
                
                if plan:
                    clear_screen()
                    display_plan(plan)
                    input("\nPress Enter to return to the main menu...")
                else:
                    print_centered("\nNo plan found with that ID")
                    time.sleep(2)
            finally:
                progress.set()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print_centered("\nThank you for using Cocolancer Travel Planner!")
        print_centered("Have a great journey! 🥥✈️")
        sys.exit(0)
