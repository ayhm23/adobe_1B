import json
import sys
import os

# Import the process_collection function from the main script
from extract1btent import load_config, process_collection

def select_collection_interactive():
    """Interactive collection selection"""
    # Use environment variable for config path if set, otherwise default
    config_path = os.environ.get('CONFIG_PATH', 'config.json')
    config = load_config(config_path)
    collections = list(config["collections"].keys())
    
    print("\n" + "="*50)
    print("ROUND 1B CHALLENGE - COLLECTION SELECTOR")
    print("="*50)
    
    print("\nAvailable collections:")
    for i, collection in enumerate(collections, 1):
        collection_config = config["collections"][collection]
        print(f"{i}. {collection}")
        print(f"   Persona: {collection_config['persona']}")
        print(f"   Job: {collection_config['job_to_be_done']}")
        print()
    
    while True:
        try:
            choice = input(f"Select collection (1-{len(collections)}) or 'all' for all collections: ").strip().lower()
            
            if choice == 'all':
                print("\nProcessing all collections...")
                for collection in collections:
                    process_collection(collection, config)
                break
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(collections):
                selected_collection = collections[choice_num - 1]
                print(f"\nProcessing: {selected_collection}")
                start_time = os.times()[4]
                # Process the selected collection
                process_collection(selected_collection, config)
                end_time = os.times()[4]
                elapsed_time = end_time - start_time    
                print(f"Processing completed in {elapsed_time:.2f} seconds")
                break
            else:
                print(f"Please enter a number between 1 and {len(collections)} or 'all'")
        
        except ValueError:
            print("Invalid input. Please enter a number or 'all'")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)

if __name__ == "__main__":
    select_collection_interactive()
