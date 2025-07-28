import json
import os
from datetime import datetime

class Round1BFormatter:
    def __init__(self, input_documents, persona, job_to_be_done, top_k=20):
        self.input_documents = input_documents
        self.persona = persona
        self.job_to_be_done = job_to_be_done
        self.top_k = top_k
        self.all_sections = []

    def add_pdf_results(self, pdf_name, sections):
        """Add results from a single PDF"""
        for section in sections:
            section_with_source = {
                'document': pdf_name,
                'heading': section['heading'],
                'score': section['score'],
                'content': section['content'],
                'page_number': section.get('page_number', 1)
            }
            self.all_sections.append(section_with_source)

    def save_round1b_output(self, output_folder):
        """Generate and save Round 1B format output"""
        # Sort by score (descending) for importance ranking
        sorted_sections = sorted(self.all_sections, key=lambda x: x['score'], reverse=True)
        
        # Limit to top K sections only
        top_sections = sorted_sections[:self.top_k]
        
        # print(f"Limiting output to top {len(top_sections)} sections (out of {len(sorted_sections)} total)")

        # Create Round 1B format
        output = {
            "metadata": {
                "input_documents": self.input_documents,
                "persona": self.persona,
                "job_to_be_done": self.job_to_be_done,
                "processing_timestamp": datetime.now().isoformat(),
                "total_sections_found": len(sorted_sections),
                "top_k_selected": len(top_sections)
            },
            "extracted_sections": [],
            "subsection_analysis": []
        }

        # Add sections in importance order (only top K)
        for idx, section in enumerate(top_sections, 1):
            # Extracted sections
            output["extracted_sections"].append({
                "document": section["document"],
                "section_title": section["heading"],
                "importance_rank": idx,
                "page_number": section["page_number"]
            })

            # Subsection analysis
            output["subsection_analysis"].append({
                "document": section["document"],
                "refined_text": section["content"],
                "page_number": section["page_number"]
            })

        # Save to file
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, "challenge1b_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Round 1B output saved to {output_path}")
        return output_path
