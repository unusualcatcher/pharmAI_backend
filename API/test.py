import json

# Define the name of your JSON file
FILENAME = 'iqvia.json'

def load_and_validate_pharma_data(filename):
    """
    Loads and validates the pharma data from the specially-formatted JSON file.
    
    This function handles two known issues:
    1. Removes the 'PHARMA_INTELLIGENCE_DB = ' variable assignment.
    2. Attempts to fix a potential extra trailing '}' brace.
    """
    
    print(f"--- Attempting to load and parse '{filename}' ---")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        print("Please make sure the file is in the same directory as this script.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # --- Step 1: Clean the file content ---
    # The file starts with 'PHARMA_INTELLIGENCE_DB = ', which is not valid JSON.
    # We must strip this part out first.
    json_text = ""
    try:
        # Split the content at the first '=' and take the second part
        json_text = file_content.split('=', 1)[1].strip()
    except IndexError:
        print("Error: File does not contain '='. It might be a standard JSON or in an unexpected format.")
        # Try to use the whole content if '=' is missing
        json_text = file_content.strip()
    except Exception as e:
        print(f"Error during initial cleaning: {e}")
        return

    # --- Step 2: Attempt to parse the cleaned JSON ---
    pharma_data = None
    try:
        # First attempt: Assume the JSON is correct *after* stripping the variable
        pharma_data = json.loads(json_text)
        print("Success: Parsed JSON on the first attempt.")
    except json.JSONDecodeError as e1:
        print(f"First parse attempt failed: {e1}")
        print("This might be due to the extra closing brace '}'. Trying to fix...")
        
        # Second attempt: Remove the last character (likely the extra '}')
        json_text_fixed = json_text.strip()[:-1]
        try:
            pharma_data = json.loads(json_text_fixed)
            print("Success: Parsed JSON on the second attempt after removing trailing character.")
        except json.JSONDecodeError as e2:
            print(f"Second parse attempt failed: {e2}")
            print("\nError: Could not parse JSON data even after attempting fixes.")
            print("Please manually inspect 'iqvia.json' for syntax errors (e.g., missing commas, extra braces).")
            return

    # --- Step 3: Run validation queries if data was loaded ---
    if pharma_data:
        print("\n--- Running Validation Queries ---")
        
        try:
            # Query 1: Check top-level keys
            print(f"\n1. Top-Level Keys:")
            print(f"   {list(pharma_data.keys())}")

            # Query 2: Access a specific molecule in 'clinical_trials' (dict)
            pirfenidone_data = pharma_data['clinical_trials']['pirfenidone']
            print(f"\n2. Pirfenidone Data:")
            print(f"   Molecule Name: {pirfenidone_data['molecule_name']}")
            print(f"   Total Trials: {pirfenidone_data['total_trials']}")

            # Query 3: Access an item in a list (active_trials)
            first_active_trial = pirfenidone_data['active_trials'][0]
            print(f"\n3. First Active Pirfenidone Trial:")
            print(f"   NCT ID: {first_active_trial['nct_id']}")
            print(f"   Title: {first_active_trial['title']}")

            # Query 4: Access deeply nested EXIM data
            metformin_export_data = pharma_data['exim_trade_data']['metformin']['api_exports_2023']['india']
            print(f"\n4. Metformin 2023 Exports from India:")
            print(f"   Value (USD Millions): {metformin_export_data['value_usd_millions']}")
            print(f"   Top Destination: {metformin_export_data['top_destinations'][0]}")

            # Query 5: Access internal knowledge base (list)
            strategy_doc = pharma_data['internal_knowledge_base']['strategic_documents']['product_innovation_strategy_2024']
            print(f"\n5. Strategic Priorities:")
            print(f"   Priority 1: {strategy_doc['key_strategic_priorities'][0]}")
            
            # Query 6: Access patent landscape data
            semaglutide_patents = pharma_data['patent_landscape']['semaglutide']['active_patents_us']
            print(f"\n6. Semaglutide Active Patents:")
            print(f"   Found {len(semaglutide_patents)} active patents.")
            print(f"   Example Patent: {semaglutide_patents[0]['title']} (Expires: {semaglutide_patents[0]['expiry_date']})")

            # Query 7: Access IQVIA market data
            ipf_market_data = pharma_data['market_intelligence_iqvia']['therapy_areas']['respiratory']['top_diseases'][2]
            print(f"\n7. IPF Market Data:")
            print(f"   Disease: {ipf_market_data['disease_name']}")
            print(f"   Market Size (USD Millions): {ipf_market_data['market_size_usd_millions']}")
            print(f"   Competition Level: {ipf_market_data['competition_level']}")

            print("\n--- All validation queries ran successfully. ---")
            print("The JSON file structure appears to be correctly formatted and accessible.")

        except KeyError as e:
            print(f"\n--- Query Failed! ---")
            print(f"Error: A 'KeyError' occurred: {e}.")
            print("This means a key we expected to find does not exist in the data.")
            print("Please check the JSON structure for this key.")
        except IndexError as e:
            print(f"\n--- Query Failed! ---")
            print(f"Error: An 'IndexError' occurred: {e}.")
            print("This means we expected an item in a list (e.g., 'active_trials') but the list was empty.")
        except Exception as e:
            print(f"\n--- Query Failed! ---")
            print(f"An unexpected error occurred during querying: {e}")

if __name__ == "__main__":
    load_and_validate_pharma_data(FILENAME)