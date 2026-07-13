import os
import sys
import fitz

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from src.prompts.individual_report_prompts import PAGE_WORD_LIMITS

def validate_pdf(pdf_path: str) -> bool:
    """
    Validates a compiled astrology report PDF for layout, content, and hyperlink correctness.
    """
    print(f"\n[Validator] Validating PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[Validator] ERROR: File not found at {pdf_path}")
        return False
        
    size_bytes = os.path.getsize(pdf_path)
    if size_bytes < 10000:
        print(f"[Validator] ERROR: PDF file is too small ({size_bytes} bytes).")
        return False
        
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[Validator] ERROR: Failed to open PDF using PyMuPDF: {e}")
        return False
        
    # 1. Page Count Validation
    total_pages = len(doc)
    print(f"[Validator] Total Pages: {total_pages}")
    if total_pages != 27:
        print(f"[Validator] ERROR: Page count is {total_pages}, expected exactly 27.")
        return False
        
    success = True
    
    # 2. Page Content and Boundary Checking
    for page_idx in range(total_pages):
        page = doc[page_idx]
        text = page.get_text().strip()
        words = text.split()
        word_count = len(words)
        images = page.get_images()
        drawings = page.get_drawings()
        
        # Check visually empty pages
        is_empty = (word_count == 0) and (len(images) == 0) and (len(drawings) == 0)
        if is_empty:
            print(f"[Validator] ERROR: Page {page_idx + 1} is completely blank/empty!")
            success = False
            continue
            
        # Target calibration word count checks
        orig_idx = page_idx - 1 if page_idx > 1 else page_idx
        if page_idx == 1:
            # Page 2 is the preformatted static template page; skip word prompt limits
            pass
        elif orig_idx in PAGE_WORD_LIMITS:
            min_w, max_w = PAGE_WORD_LIMITS[orig_idx]
            
            # Since standard template headers/footers add about 20-30 words, 
            # we subtract template words when validating generated text density.
            # To be safe, we check that total words is at least 30 words higher than template size.
            if orig_idx == 5: # Page 6 short chart text
                if word_count < 10:
                    print(f"[Validator] WARNING: Page {page_idx + 1} underfilled. Word count = {word_count} (expected short description).")
            elif orig_idx == 24: # Page 26 Remedies
                # Remedies has custom bullets and lines
                if word_count < 40:
                    print(f"[Validator] WARNING: Page {page_idx + 1} remedies underfilled. Word count = {word_count}.")
            else:
                # Standard text pages check
                if word_count < (min_w - 30):
                    print(f"[Validator] ERROR: Page {page_idx + 1} is underfilled. Word count = {word_count} (min expected: {min_w}).")
                    success = False
                elif word_count > (max_w + 50): # Allow small buffer for headers/footers
                    print(f"[Validator] WARNING: Page {page_idx + 1} might be overfilled or overflowing. Word count = {word_count} (max text limit: {max_w}).")
                    
        # 3. Remedies Hyperlinks Verification (Page 26, index 25)
        if page_idx == 25:
            links = page.get_links()
            print(f"[Validator] Page 26 Remedies Links count: {len(links)}")
            
            has_bracelet_link = False
            has_consult_link = False
            has_rudraksha_link = False
            
            for l in links:
                uri = l.get("uri", "")
                if "product/divy-love-bracelet" in uri:
                    has_bracelet_link = True
                elif "kundli-analysis" in uri:
                    has_consult_link = True
                elif "product/" in uri and "rudraksha" in uri:
                    has_rudraksha_link = True
                    
            if not has_bracelet_link:
                print("[Validator] ERROR: Page 26 is missing clickable Divy Love Bracelet hyperlink overlay.")
                success = False
            if not has_consult_link:
                print("[Validator] ERROR: Page 26 is missing clickable Live Consultation hyperlink overlay.")
                success = False
            if not has_rudraksha_link:
                print("[Validator] ERROR: Page 26 is missing clickable dynamic Rudraksha hyperlink overlay.")
                success = False
                
            if has_bracelet_link and has_consult_link and has_rudraksha_link:
                print("[Validator] SUCCESS: Page 26 Remedies hyperlinks verified correctly.")
                
    doc.close()
    if success:
        print("[Validator] SUCCESS: PDF report validation passed completely!\n")
    else:
        print("[Validator] FAILED: PDF report validation failed on layout/links.\n")
    return success

if __name__ == "__main__":
    test_pdf = os.path.join(backend_dir, "output", "Sugandha_report.pdf")
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
    validate_pdf(test_pdf)
