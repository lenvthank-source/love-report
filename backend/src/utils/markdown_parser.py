import re

def strip_thinking_tags(text: str) -> str:
    """
    Strips out <think>...</think> and <thinking>...</thinking> blocks from the model's response,
    including the tags themselves and any contents within them.
    Handles multi-line thinking blocks using re.DOTALL.
    """
    if not text:
        return ""
    # Strip <think>...</think> (used by Qwen/DeepSeek)
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip <thinking>...</thinking> (used by other reasoning models)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Strip stray thinking tags
    cleaned = re.sub(r'<(?:think|thinking)>\s*</(?:think|thinking)>', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def strip_page_references(text: str) -> str:
    """
    Removes any line that starts with 'Page' followed by a number, e.g.:
      - 'Page 13 – The D1 Natal Promise vs. The D9 Navamsa Fruit'
      - 'Page 14 of 26'
      - '*Page 5: Master Index*'
    These are AI-generated artefacts and must never appear in body text.
    """
    if not text:
        return text
    cleaned = []
    for line in text.splitlines():
        # Skip lines where (after optional markdown symbols) 'Page N' appears
        if re.match(r'^\s*[*_\-#>\s]*Page\s+\d+', line, re.IGNORECASE):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def parse_markdown_to_html(text: str) -> str:
    """
    Converts basic markdown syntax to standard HTML tags:
    - **bold** -> <strong>bold</strong>
    - *italics* -> <em>italics</em>
    - ## Header -> <h2>Header</h2>
    - ### Subheader -> <h3>Subheader</h3>
    - > Blockquote -> <blockquote>Blockquote</blockquote>
    - - List item -> <li>List item</li>
    """
    if not text:
        return ""

    # Strip AI page-reference artefacts first
    text = strip_page_references(text)

    # 1. Clean HTML characters first (escape raw & and < to avoid rendering issues)
    text = text.replace("&", "&amp;")

    # Keep standard tag conversions clean
    lines = text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # Headers (no raw ## characters in final output)
        if line_str.startswith("###"):
            title = line_str.replace("###", "").strip()
            html_lines.append(f"<h3>{title}</h3>")
        elif line_str.startswith("##"):
            title = line_str.replace("##", "").strip()
            html_lines.append(f"<h2>{title}</h2>")
        # Blockquotes
        elif line_str.startswith(">"):
            quote = line_str.replace(">", "").strip()
            html_lines.append(f"<blockquote>{quote}</blockquote>")
        # Bullet list items
        elif line_str.startswith("-") or line_str.startswith("*"):
            bullet = line_str[1:].strip()
            html_lines.append(f"<li>{bullet}</li>")
        # Standard paragraph
        else:
            html_lines.append(f"<p>{line_str}</p>")

    html_text = "\n".join(html_lines)

    # Convert bold markers (**word** or __word__) to <strong>
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)

    # Convert italics markers (*word* or _word_) to <em>
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
    html_text = re.sub(r'_(.*?)_', r'<em>\1</em>', html_text)

    # Clean up empty paragraph tags
    html_text = html_text.replace("<p></p>", "")

    return html_text
