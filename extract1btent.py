import fitz  # PyMuPDF
import re
import os
import glob
import json
import sys
from collections import Counter

# Import from our new src modules
from src.heading_extractor import extract_heading_candidates, extract_sections_from_headings
from src.semantic_matcher import match_to_job_query
from src.text_utils import clean_text
from src.round1b_formatter import Round1BFormatter


def load_config(config_path="config.json"):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file '{config_path}' not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def process_collection(collection_name, config):
    """Process a specific collection"""
    if collection_name not in config["collections"]:
        print(f"Collection '{collection_name}' not found in configuration!")
        print(f"Available collections: {list(config['collections'].keys())}")
        return
    
    collection_config = config["collections"][collection_name]
    output_settings = config["output_settings"]
    
    input_folder = collection_config["input_folder"]
    output_folder = output_settings["output_folder"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {collection_name}")
    print(f"Input folder: {input_folder}")
    print(f"Persona: {collection_config['persona']}")
    print(f"Job: {collection_config['job_to_be_done']}")
    print(f"{'='*60}")

    os.makedirs(output_folder, exist_ok=True)
    pdf_paths = glob.glob(os.path.join(input_folder, "*.pdf"))
    
    if not pdf_paths:
        print(f"No PDF files found in {input_folder}")
        return

    # Define your configuration for Round 1B format
    input_documents = [os.path.basename(pdf_path) for pdf_path in pdf_paths]
    persona = collection_config["persona"]
    job_to_be_done = collection_config["job_to_be_done"]
    job_query = collection_config["job_query"]
    top_k_matches = output_settings["top_k_matches"]
    top_k_output = output_settings.get("top_k_output", 20)  # Default to 20 if not specified

    # Initialize Round 1B formatter with top_k limit
    formatter = Round1BFormatter(input_documents, persona, job_to_be_done, top_k=top_k_output)

    print(f"Found {len(pdf_paths)} PDF files to process")
    # print(f"Will extract top {top_k_matches} matches per PDF")
    # print(f"Final output limited to top {top_k_output} sections overall")

    for pdf_path in pdf_paths:
        pdf_name = os.path.basename(pdf_path)
        print(f"\nProcessing: {pdf_name}")
        
        try:
            candidates = extract_heading_candidates(pdf_path)
            print(f"Found {len(candidates)} heading candidates.")

            if not candidates:
                print(f"No candidates found in {pdf_name}, skipping...")
                continue
            
            top_matches = match_to_job_query(candidates, job_query, top_k=top_k_matches)
            # print(f"Top {len(top_matches)} Matching Headings:")
            # for idx, match in enumerate(top_matches):
            #     print(f"{idx+1}. {match['text']} (Score: {match['score']}) [Page: {match['page_num']+1}]")

            if not top_matches:
                print(f"No matching sections found in {pdf_name}, skipping...")
                continue

            sections = extract_sections_from_headings(pdf_path, top_matches)

            # Add to Round 1B formatter
            formatter.add_pdf_results(pdf_name, sections)

            # Prepare individual results if enabled
            if output_settings["save_individual_results"]:
                out_data = []
                for section in sections:
                    out_data.append({
                        "heading": section["heading"],
                        "score": section["score"],
                        "content": section["content"],
                        "page_number": section.get("page_number", 1)
                    })
                    # print(f"\n### {section['heading']} (Score: {section['score']}) [Page: {section.get('page_number', 1)}]")
                    # print(section["content"][:500] + "..." if len(section["content"]) > 500 else section["content"])

                # Save individual results
                out_json_path = os.path.join(
                    output_folder,
                    os.path.basename(pdf_path).replace('.pdf', '_results.json')
                )
                with open(out_json_path, "w", encoding="utf-8") as f:
                    json.dump(out_data, f, ensure_ascii=False, indent=2)
                print(f"Individual results saved to {out_json_path}")
            else:
                print(f"Processed {len(sections)} sections from {pdf_name}")
                
        except Exception as e:
            print(f"Error processing {pdf_name}: {str(e)}")
            continue
    
    # Generate Round 1B output after processing all PDFs
    print("\n" + "="*50)
    print("Generating Round 1B format output...")
    try:
        output_path = formatter.save_round1b_output(output_folder)
        print(f"✓ Round 1B output saved to: {output_path}")
        print(f"✓ Limited to top {top_k_output} sections from {len(formatter.all_sections)} total found")
    except Exception as e:
        print(f"Error generating Round 1B output: {str(e)}")
    print("="*50)


if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Collection selection - CHANGE THIS LINE to process different collections
    collection_to_process = "Collection 1"  # Options: "Collection 1", "Collection 2", "Collection 3"
    
    print("\n" + "="*60)
    print("ROUND 1B CHALLENGE - COLLECTION PROCESSOR")
    print("="*60)
    print(f"Available collections: {list(config['collections'].keys())}")
    print(f"🎯 CURRENTLY PROCESSING: {collection_to_process}")
    print(f"📁 Input folder: {config['collections'][collection_to_process]['input_folder']}")
    print(f"👤 Persona: {config['collections'][collection_to_process]['persona']}")
    print(f"🎯 Job: {config['collections'][collection_to_process]['job_to_be_done']}")
    print("="*60)
    
    # Ask for confirmation
    confirm = input(f"\nContinue with {collection_to_process}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        exit()
    
    process_collection(collection_to_process, config)

