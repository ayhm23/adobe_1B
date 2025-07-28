import fitz  # PyMuPDF
import re
import numpy as np
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait
import time
from .text_utils import clean_text, is_bold_font, is_all_upper, is_title_case, is_binary_data

# Try to import PaddleOCR, but make it optional
try:
    from paddleocr import LayoutDetection
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("Warning: PaddleOCR not available. Using heuristic-only extraction.")


class HybridHeadingExtractor:
    def __init__(self, enable_layout_detection=False):
        self.layout_cache = {}  # Cache for layout results
        self.layout_model = None
        
        # Initialize layout model with CPU-only settings
        if enable_layout_detection and PADDLEOCR_AVAILABLE:
            try:
                print("Initializing PaddleOCR layout detection model (CPU-only)...")
                print("This may take a moment on first run...")
                
                # Docker/Linux path
                import os
                MODEL_DIR = "/app/models/PP-DocLayout-M"
                
                # Fallback to local development path if Docker path doesn't exist
                if not os.path.exists(MODEL_DIR):
                    if os.name == 'nt':  # Windows
                        MODEL_DIR = r"C:\Users\archi\OneDrive\Desktop\New folder (2)\Adobe1B\models\PP-DocLayout-M"
                    else:  # Linux/WSL
                        MODEL_DIR = "/mnt/c/Users/archi/OneDrive/Desktop/New folder (2)/Adobe1B/models/PP-DocLayout-M"
                
                # Check if model directory exists
                if not os.path.exists(MODEL_DIR):
                    print(f"⚠ Model directory not found: {MODEL_DIR}")
                    print("Available model directories:")
                    base_models_dir = os.path.dirname(MODEL_DIR)
                    if os.path.exists(base_models_dir):
                        for item in os.listdir(base_models_dir):
                            print(f"  - {item}")
                    else:
                        print(f"  Base models directory doesn't exist: {base_models_dir}")
                    raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
                
                # CPU-only initialization with explicit settings
                os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Force CPU usage
                
                # Initialize layout detection model
                self.layout_model = LayoutDetection(
                    model_dir=MODEL_DIR,
                    use_gpu=False,  # Force CPU usage
                    cpu_threads=2   # Limit CPU threads for Docker
                )
                print(f"✓ Layout detection model initialized from: {MODEL_DIR}")
                
            except Exception as e:
                print(f"⚠ Failed to initialize layout detection: {e}")
                print("  Falling back to heuristic-only extraction")
                self.layout_model = None
                PADDLEOCR_AVAILABLE = False
        else:
            print("Layout detection disabled or PaddleOCR not available")

    def extract_headings_hybrid(self, doc, job_query=""):
        """Main method that combines layout detection and heuristic approaches"""
        if not self.layout_model:
            print("  🔍 Using heuristic extraction only...")
            return self._run_heuristic_extraction(doc)
        
        print("  🔄 Running hybrid extraction (Layout + Heuristic)...")
        
        # Run both approaches in parallel for speed
        with ThreadPoolExecutor(max_workers=2) as executor:
            print("  ⏳ Starting parallel extraction...")
            layout_future = executor.submit(self._run_layout_detection, doc)
            heuristic_future = executor.submit(self._run_heuristic_extraction, doc)
            
            # Wait for both to complete with timeout
            try:
                print("  ⏳ Waiting for layout detection...")
                layout_headings = layout_future.result(timeout=300)
                print(f"  ✓ Layout detection complete. Found {len(layout_headings)} headings.")
                
                print("  ⏳ Waiting for heuristic extraction...")
                heuristic_headings = heuristic_future.result(timeout=300)
                print(f"  ✓ Heuristic extraction complete. Found {len(heuristic_headings)} headings.")
                
            except Exception as e:
                print(f"  ❌ Error in parallel extraction: {e}")
                # Fallback to heuristic only if parallel processing fails
                return self._run_heuristic_extraction(doc)
        
        # Merge and rank results
        print("  🔄 Merging results...")
        merged_headings = self._merge_heading_results(
            layout_headings, heuristic_headings, doc
        )
        print(f"  ✓ Merged into {len(merged_headings)} headings.")
        
        # Apply semantic matching
        print("  🎯 Applying semantic matching...")
        result = self._apply_semantic_matching(merged_headings, job_query)
        print(f"  ✓ Semantic matching complete. Final count: {len(result)}")
        return result
    
    def _run_layout_detection(self, doc):
        """Extract headings using PP-DocLayout-M"""
        if not self.layout_model:
            print("    ⚠️ No layout model available")
            return []
            
        layout_headings = []
        print(f"    🔍 Running layout detection on {len(doc)} pages...")
        
        for page_num, page in enumerate(doc):
            print(f"      📄 Processing page {page_num + 1}/{len(doc)}")
            
            # Convert page to image and save as temporary file
            pix = page.get_pixmap(dpi=150, alpha=False)  # 150 DPI for speed
            
            # Create temporary image file path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_image_path = temp_file.name
                # Save the image
                pix.save(temp_image_path)
            
            # Run layout detection
            try:
                results = self.layout_model.predict(temp_image_path, batch_size=1)
                print(f"        ✓ Layout detection completed for page {page_num + 1}")
                
                # Extract heading-related boxes
                heading_boxes = []
                for result in results:
                    for box in result.get('boxes', []):
                        label = box.get('label', '')
                        if label in ['paragraph_title', 'doc_title']:
                            heading_boxes.append({
                                'bbox': box['coordinate'],  # [x0, y0, x1, y1]
                                'confidence': box['score'],
                                'type': label,
                                'page_num': page_num
                            })
                
                print(f"        📦 Found {len(heading_boxes)} heading boxes on page {page_num + 1}")
                
                # Extract text from detected boxes
                page_headings = self._extract_text_from_boxes(page, heading_boxes)
                print(f"        📝 Extracted {len(page_headings)} headings from page {page_num + 1}")
                layout_headings.extend(page_headings)
                
            except Exception as e:
                print(f"        ❌ Layout detection failed for page {page_num}: {e}")
                continue
            finally:
                # Clean up temporary file with retry
                try:
                    import os
                    import time
                    # Small delay to ensure file is not locked
                    time.sleep(0.1)
                    if os.path.exists(temp_image_path):
                        os.unlink(temp_image_path)
                except Exception as cleanup_error:
                    print(f"        ⚠️ Could not clean up temp file: {cleanup_error}")
                    pass
        
        print(f"    ✓ Layout detection complete. Total headings: {len(layout_headings)}")
        return layout_headings

    def _extract_text_from_boxes(self, page, heading_boxes):
        """Extract text from PP-DocLayout detected boxes using PyMuPDF"""
        headings = []
        words = page.get_text("words")  # Get all words with coordinates
        
        for box in heading_boxes:
            x0, y0, x1, y1 = box['bbox']
            
            # Find words within the bounding box
            box_words = []
            for word in words:
                wx0, wy0, wx1, wy1, text = word[:5]
                
                # Filter out binary data immediately
                if is_binary_data(text):
                    continue
                
                # Check if word overlaps with detected box (with tolerance)
                if (wx0 >= x0-5 and wy0 >= y0-5 and 
                    wx1 <= x1+5 and wy1 <= y1+5):
                    box_words.append((wx0, text))
            
            # Sort words by x-coordinate and join
            if box_words:
                box_words.sort(key=lambda w: w[0])
                heading_text = ' '.join([w[1] for w in box_words])
                
                # Clean and validate the final text
                cleaned_text = clean_text(heading_text)
                if cleaned_text and not is_binary_data(cleaned_text):
                    headings.append({
                        'text': cleaned_text,
                        'page_num': box['page_num'],
                        'y': y0,
                        'x': x0,
                        'confidence': box['confidence'],
                        'source': f"layout_{box['type']}",
                        'bbox': box['bbox']
                    })
        
        return headings

    def _run_heuristic_extraction(self, doc):
        """Your existing heuristic approach with optimizations"""
        return self.extract_heading_candidates_optimized(doc)
    
    def extract_heading_candidates_optimized(self, doc):
        """Optimized version of your existing function"""
        candidates = []
        all_lines = []
        
        # Your existing logic here, but with these optimizations:
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            
            # Add early termination for very long documents
            if len(all_lines) > 1000:  # Prevent memory issues
                break
                
            # Your existing span processing...
            spans = []
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        spans.append({
                            "text": span["text"],
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],
                            "x0": span["bbox"][0],
                            "x1": span["bbox"][2],
                            "y0": span["bbox"][1],
                            "y1": span["bbox"][3],
                            "origin_y": line["bbox"][1],
                            "page_width": page.rect.width,
                            "page_num": page_num
                        })

            spans.sort(key=lambda s: (round(s["origin_y"], 1), s["x0"]))

            merged_lines = []
            buffer = ""
            last_y = None
            last_size = None
            last_span = None

            for span in spans:
                raw_text = span["text"]
                
                # Filter out binary data immediately
                if is_binary_data(raw_text):
                    continue
                    
                text = clean_text(raw_text)
                if not text:
                    continue

                current_y = round(span["origin_y"], 1)
                size = span["size"]
                is_new_para = False
                if last_y is not None and abs(current_y - last_y) > size * 1.2:
                    is_new_para = True

                if buffer and (re.search(r"[.?!]$", buffer) or is_new_para):
                    merged_lines.append((buffer.strip(), last_size, last_span))
                    buffer = text
                else:
                    buffer = buffer + " " + text if buffer else text

                last_y = current_y
                last_size = size
                last_span = span

            if buffer:
                merged_lines.append((buffer.strip(), last_size, last_span))

            all_lines.extend(merged_lines)

        line_widths = [span["x1"] - span["x0"] for _, _, span in all_lines]
        if not line_widths:
            return []

        rounded_widths = [round(w, -1) for w in line_widths]
        most_common_width = Counter(rounded_widths).most_common(1)[0][0]
        threshold_width = 0.75 * most_common_width

        font_sizes = [line[1] for line in all_lines]
        median_font_size = sorted(font_sizes)[len(font_sizes) // 2] if font_sizes else 12

        for sentence, size, span in all_lines:
            flags = span["flags"]
            page_width = span["page_width"]
            text_width = span["x1"] - span["x0"]

            is_bold = is_bold_font(span)
            is_italic = (flags & 1) != 0
            is_centered = abs(span["x0"] - (page_width - span["x1"])) < 20

            word_count = len(sentence.split())
            reasons = []

            if size > median_font_size * 1.15:
                reasons.append("Larger font size")
            if is_bold:
                reasons.append("Bold font")
            if is_italic:
                reasons.append("Italic font")
            if is_centered and (text_width < threshold_width or word_count < 10):
                reasons.append("Center aligned (short line)")
            if is_all_upper(sentence):
                reasons.append("All uppercase")
            if is_title_case(sentence):
                reasons.append("Title case")
            if word_count < 10 and size > median_font_size:
                reasons.append("Short & prominent")

            if reasons:
                candidates.append({
                    "text": sentence,
                    "size": size,
                    "bold": is_bold,
                    "italic": is_italic,
                    "centered": is_centered,
                    "words": word_count,
                    "width": text_width,
                    "reasons": reasons,
                    "page_num": span["page_num"],
                    "y": span["y0"],
                    "x0": span["x0"]
                })
        
        # Convert to consistent format
        formatted_candidates = []
        for candidate in candidates:
            formatted_candidates.append({
                'text': candidate['text'],
                'page_num': candidate['page_num'],
                'y': candidate['y'],
                'x': candidate.get('x0', 0),
                'confidence': 0.7,  # Default heuristic confidence
                'source': 'heuristic',
                'reasons': candidate['reasons']
            })
        
        return formatted_candidates
    
    def _merge_heading_results(self, layout_headings, heuristic_headings, doc):
        """Merge results from both approaches intelligently"""
        merged = []
        used_heuristic_indices = set()
        
        # First, add all layout-detected headings (higher confidence)
        for layout_heading in layout_headings:
            layout_heading['method'] = 'layout'
            merged.append(layout_heading)
            
            # Find and mark nearby heuristic headings as used
            for i, heuristic_heading in enumerate(heuristic_headings):
                if (layout_heading['page_num'] == heuristic_heading['page_num'] and
                    abs(layout_heading['y'] - heuristic_heading['y']) < 20):
                    used_heuristic_indices.add(i)
        
        # Add remaining heuristic headings (fallback for missed detections)
        for i, heuristic_heading in enumerate(heuristic_headings):
            if i not in used_heuristic_indices:
                # Only add if it meets quality criteria
                reasons = heuristic_heading.get('reasons', [])
                if ('Larger font size' in reasons or 'Bold font' in reasons or 
                    len(heuristic_heading['text'].split()) <= 8):
                    # Convert format to match layout headings
                    merged.append({
                        'text': heuristic_heading['text'],
                        'page_num': heuristic_heading['page_num'],
                        'y': heuristic_heading['y'],
                        'x': heuristic_heading.get('x', 0),
                        'confidence': 0.7,  # Default confidence for heuristic
                        'source': 'heuristic',
                        'method': 'heuristic',
                        'reasons': heuristic_heading.get('reasons', [])
                    })
        
        # Sort by page and y-coordinate
        merged.sort(key=lambda h: (h['page_num'], h['y']))
        
        return merged
    
    def _apply_semantic_matching(self, headings, job_query):
        """Apply semantic matching to the merged headings"""
        from .semantic_matcher import match_to_job_query
        
        # Convert to format expected by semantic matcher
        candidates = []
        for heading in headings:
            candidates.append({
                'text': heading['text'],
                'page_num': heading['page_num'],
                'y': heading['y']
            })
        
        # Get the semantic matches with scores
        semantic_matches = match_to_job_query(candidates, job_query)
        
        # Add the semantic scores back to the original headings
        scored_headings = []
        for match in semantic_matches:
            # Find the original heading that matches this semantic result
            for heading in headings:
                if (heading['text'] == match['text'] and 
                    heading['page_num'] == match['page_num'] and 
                    abs(heading['y'] - match['y']) < 1):
                    # Create a new heading with the score added
                    scored_heading = heading.copy()
                    scored_heading['score'] = match['score']
                    scored_headings.append(scored_heading)
                    break
        
        return scored_headings


def extract_heading_candidates_from_doc(doc):
    """Extract potential heading candidates from a PDF document based on formatting characteristics"""
    candidates = []
    all_lines = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        spans = []

        for block in blocks:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    spans.append({
                        "text": span["text"],
                        "font": span["font"],
                        "size": span["size"],
                        "flags": span["flags"],
                        "x0": span["bbox"][0],
                        "x1": span["bbox"][2],
                        "y0": span["bbox"][1],
                        "y1": span["bbox"][3],
                        "origin_y": line["bbox"][1],
                        "page_width": page.rect.width,
                        "page_num": page_num
                    })

        spans.sort(key=lambda s: (round(s["origin_y"], 1), s["x0"]))

        merged_lines = []
        buffer = ""
        last_y = None
        last_size = None
        last_span = None

        for span in spans:
            raw_text = span["text"]
            
            # Filter out binary data immediately
            if is_binary_data(raw_text):
                continue
                
            text = clean_text(raw_text)
            if not text:
                continue

            current_y = round(span["origin_y"], 1)
            size = span["size"]
            is_new_para = False
            if last_y is not None and abs(current_y - last_y) > size * 1.2:
                is_new_para = True

            if buffer and (re.search(r"[.?!]$", buffer) or is_new_para):
                merged_lines.append((buffer.strip(), last_size, last_span))
                buffer = text
            else:
                buffer = buffer + " " + text if buffer else text

            last_y = current_y
            last_size = size
            last_span = span

        if buffer:
            merged_lines.append((buffer.strip(), last_size, last_span))

        all_lines.extend(merged_lines)

    line_widths = [span["x1"] - span["x0"] for _, _, span in all_lines]
    if not line_widths:
        return []

    rounded_widths = [round(w, -1) for w in line_widths]
    most_common_width = Counter(rounded_widths).most_common(1)[0][0]
    threshold_width = 0.75 * most_common_width

    font_sizes = [line[1] for line in all_lines]
    median_font_size = sorted(font_sizes)[len(font_sizes) // 2] if font_sizes else 12

    for sentence, size, span in all_lines:
        flags = span["flags"]
        page_width = span["page_width"]
        text_width = span["x1"] - span["x0"]

        is_bold = is_bold_font(span)
        is_italic = (flags & 1) != 0
        is_centered = abs(span["x0"] - (page_width - span["x1"])) < 20

        word_count = len(sentence.split())
        reasons = []

        if size > median_font_size * 1.15:
            reasons.append("Larger font size")
        if is_bold:
            reasons.append("Bold font")
        if is_italic:
            reasons.append("Italic font")
        if is_centered and (text_width < threshold_width or word_count < 10):
            reasons.append("Center aligned (short line)")
        if is_all_upper(sentence):
            reasons.append("All uppercase")
        if is_title_case(sentence):
            reasons.append("Title case")
        if word_count < 10 and size > median_font_size:
            reasons.append("Short & prominent")

        if reasons:
            candidates.append({
                "text": sentence,
                "size": size,
                "bold": is_bold,
                "italic": is_italic,
                "centered": is_centered,
                "words": word_count,
                "width": text_width,
                "reasons": reasons,
                "page_num": span["page_num"],
                "y": span["y0"]
            })

    return candidates

# Keep the original function for backward compatibility
def extract_heading_candidates(pdf_path):
    """Extract potential heading candidates from a PDF based on formatting characteristics"""
    doc = fitz.open(pdf_path)
    return extract_heading_candidates_from_doc(doc)


def extract_sections_from_headings(pdf_path, heading_matches):
    """Extract text sections based on identified headings"""
    doc = fitz.open(pdf_path)

    sorted_matches = sorted(heading_matches, key=lambda x: (x["page_num"], x["y"]))
    sections = []

    for i, current in enumerate(sorted_matches):
        start_page = current["page_num"]
        start_y = current["y"]
        end_page = doc.page_count - 1
        end_y = None

        if i + 1 < len(sorted_matches):
            next_heading = sorted_matches[i + 1]
            end_page = next_heading["page_num"]
            end_y = next_heading["y"]

        section_text = ""
        for p in range(start_page, end_page + 1):
            page = doc[p]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    line_y = line["bbox"][1]
                    if (p == start_page and line_y < start_y) or (p == end_page and end_y is not None and line_y >= end_y):
                        continue
                    for span in line["spans"]:
                        section_text += span["text"] + " "
            section_text += "\n"

        sections.append({
            "heading": current["text"],
            "score": current.get("score", 0.0),  # Default score if missing
            "content": clean_text(section_text),
            "page_number": start_page + 1  # Convert to 1-based page numbering
        })

    return sections
