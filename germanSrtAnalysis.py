#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
German SRT Morphological Analyzer

A flexible text analysis tool using spaCy to extract parts of speech 
(Nouns, Verbs, Adjectives, Adverbs) within their context from subtitle files (.srt).

Features:
- Generates 10 reports: 5 HTML and 5 Markdown files.
- Output organized in an "Analyse" folder.
- HTML reports include:
    - Hyperlinks to Verbformen.es (using the original inflected word).
    - Hyperlinks to localhost timestamps for video integration.
    - Context highlighting.

Usage (inside active venv):
python germanSrtAnalysis.py input_file.srt
"""

import spacy
import sys
import os
import argparse
import re
import html
import urllib.parse

# --- Configuration ---
# Mapping internal keys to spaCy POS tags and display titles
POS_MAP = {
    'adj':  ('ADJ',  'Adjectives'),
    'verb': ('VERB', 'Verbs'),
    'nom':  ('NOUN', 'Nouns'),
    'adv':  ('ADV',  'Adverbs')
}

# German definite articles mapping for nouns
ARTICLE_MAP = {
    'Masc': 'der',
    'Fem':  'die',
    'Neut': 'das'
}

LOCALHOST_PORT = 8080 

# --- Helper Functions ---

def load_model():
    """Attempts to load the large German spaCy model."""
    try:
        return spacy.load("de_core_news_lg")
    except IOError:
        sys.stderr.write("\nERROR: spaCy model 'de_core_news_lg' not found.\n")
        sys.stderr.write("Please install it using: python -m spacy download de_core_news_lg\n")
        sys.exit(1)

def read_file(filename):
    """Reads the content of the specified file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        sys.stderr.write(f"\nERROR: File '{filename}' not found.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"\nAn error occurred while reading the file: {e}\n")
        sys.exit(1)

def get_article_from_token(token):
    """Determines the nominative article (der, die, das) for a Noun token."""
    morph = token.morph
    number_list = morph.get('Number')
    # Plural takes precedence
    if number_list and number_list[0] == 'Plur':
        return 'die'
    
    gender_list = morph.get('Gender')
    if gender_list:
        gender = gender_list[0]
        return ARTICLE_MAP.get(gender, '')
    return ''

def get_final_lemma(token):
    """Returns the lemma, automatically adding the article for nouns."""
    lemma = token.lemma_
    if token.pos_ == 'NOUN':
        article = get_article_from_token(token)
        if article:
            lemma = f"{article} {lemma}"
    return lemma

# --- Formatting Helper Functions ---

def get_html_cell_content(matches_dict):
    """
    Formats matches for an HTML cell (<strong>, <br>, and <a> hyperlink).
    Logic: Links to verbformen.es using the ORIGINAL text (token.text).
    """
    if not matches_dict:
        return ""
    
    links = []
    # matches_dict structure: {'der Mann': {'Mann', 'Mannes'}, 'die Frau': {'Frau'}}
    for lemma, original_texts in sorted(matches_dict.items()):
        display_lemma = html.escape(lemma)
        
        # Pick ONE of the original words for the URL generation
        original_word_for_url = list(original_texts)[0] 
            
        # URL encode the original word (handles umlauts safely)
        url_encoded_word = urllib.parse.quote_plus(original_word_for_url)
        url = f"https://www.verbformen.es/?w={url_encoded_word}"
        
        # Display the Lemma, but link using the original word
        links.append(f'<a href="{url}" target="_blank" title="Lookup: {original_word_for_url}"><strong>{display_lemma}</strong></a>')
    
    return "<br>".join(links)


def get_md_cell_content(matches_dict):
    """
    Formats matches for a Markdown cell (backticks and spaces).
    """
    if not matches_dict:
        return ""
    # We only need the keys (lemmas) for Markdown
    lemmas = sorted(matches_dict.keys())
    sanitized_lemmas = [g.replace('`', r'\`') for g in lemmas]
    return " ".join([f"`{g}`" for g in sanitized_lemmas])

def get_html_header(title):
    """Returns the HTML header including CSS styles."""
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; margin: 2em; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse;
            margin-bottom: 2em;
            table-layout: fixed;
        }}
        th, td {{ 
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
            vertical-align: top;
            word-wrap: break-word;
        }}
        th {{ background-color: #f4f4f4; }}
        
        /* Individual Reports: Context (60%), Matches (30%), Time (10%) */
        .single-report th:nth-child(1), .single-report td:nth-child(1) {{ width: 60%; }}
        .single-report th:nth-child(2), .single-report td:nth-child(2) {{ width: 30%; }}
        .single-report th:nth-child(3), .single-report td:nth-child(3) {{ width: 10%; font-size: 0.9em; color: #555; }}
        
        /* Combined Report: Context (30%), 4x Matches (15% each), Time (10%) */
        .combined th:nth-child(1), .combined td:nth-child(1) {{ width: 30%; }}
        .combined th:nth-child(2), .combined td:nth-child(2) {{ width: 15%; }}
        .combined th:nth-child(3), .combined td:nth-child(3) {{ width: 15%; }}
        .combined th:nth-child(4), .combined td:nth-child(4) {{ width: 15%; }}
        .combined th:nth-child(5), .combined td:nth-child(5) {{ width: 15%; }}
        .combined th:nth-child(6), .combined td:nth-child(6) {{ width: 10%; font-size: 0.9em; color: #555; }}

        h1, h2, h3, h4 {{ border-bottom: 2px solid #f4f4f4; padding-bottom: 5px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        strong {{ color: #333; }}
        td strong.highlight {{ background-color: #fff8c5; padding: 0 2px; }}
        
        /* Link Styles */
        a {{ text-decoration: none; color: #005fcc; }}
        a:hover {{ text-decoration: underline; }}
        /* Make timestamp links less obtrusive */
        td:nth-child(3) a, .combined td:nth-child(6) a {{ color: #444; }} 
    </style>
</head>
<body>
"""

# --- Main Logic (Analysis) ---

def analyze_text_and_create_data(nlp, raw_text):
    """
    Analyzes the raw text by parsing SRT blocks to extract timestamps
    and linguistic data.
    
    Returns:
        - List of sentence dictionaries (for tables)
        - Dictionary of global unique lemmas mapping to original texts
        - Dictionary of total counts
    """
    
    sentence_reports = [] 
    # global_lemmas_map stores { 'verb': {'lassen': {'Lass'}, ...}, ...}
    global_lemmas_map = {key: {} for key in POS_MAP.keys()}
    global_totals = {key: 0 for key in POS_MAP.keys()}

    # Regex to find SRT timestamps (Start time --> End time)
    # We capture group 1 (Start time)
    timestamp_regex = re.compile(r'(\d{1,2}:\d{2}:\d{2},\d{3}) --> \d{1,2}:\d{2}:\d{2},\d{3}')
    
    # Split text into blocks based on double newlines (standard SRT format)
    srt_blocks = re.split(r'\n{2,}', raw_text)

    for block in srt_blocks:
        block = block.strip()
        if not block:
            continue

        timestamp_match = timestamp_regex.search(block)
        
        if not timestamp_match:
            continue
            
        timestamp = timestamp_match.group(1)
        
        # Extract text after the timestamp
        text_content_raw = block[timestamp_match.end():].strip()
        # Clean HTML tags often found in subtitles (e.g., <i>)
        text_content_clean = re.sub(r'<[^>]+>', ' ', text_content_raw).strip()
        
        if not text_content_clean:
            continue

        # Process this specific block with spaCy
        doc_chunk = nlp(text_content_clean)
            
        # matches_in_sentence_map stores { 'nom': {'der Mann': {'Mannes'}}, ...}
        matches_in_sentence_map = {key: {} for key in POS_MAP.keys()}
        matches_in_sentence_tokens = {key: [] for key in POS_MAP.keys()}
        
        for token in doc_chunk:
            # Identify if token matches one of our target POS tags
            selection_key = next((key for key, (pos_val, _) in POS_MAP.items() if pos_val == token.pos_), None)
            
            if selection_key:
                lemma = get_final_lemma(token)
                original_text = token.text
                
                # 1. Populate Sentence Data
                if lemma not in matches_in_sentence_map[selection_key]:
                    matches_in_sentence_map[selection_key][lemma] = set()
                matches_in_sentence_map[selection_key][lemma].add(original_text)

                # 2. Populate Global Data (Summary)
                if lemma not in global_lemmas_map[selection_key]:
                    global_lemmas_map[selection_key][lemma] = set()
                global_lemmas_map[selection_key][lemma].add(original_text)
                
                matches_in_sentence_tokens[selection_key].append(token)
                global_totals[selection_key] += 1

        # Skip block if no relevant words found
        if not any(matches_in_sentence_map.values()):
            continue
        
        # Prepare Context Strings
        context_md = text_content_clean.replace("|", "\|").replace("\n", " ")
        context_html_plain = html.escape(text_content_clean).replace("\n", "<br>")
        
        highlighted_contexts_map = {}
        
        # Generate highlighted HTML context for each category
        for key in POS_MAP.keys():
            tokens_to_highlight = {t.i for t in matches_in_sentence_tokens[key]}
            
            if not tokens_to_highlight:
                highlighted_contexts_map[key] = context_html_plain
                continue

            highlighted_str = ""
            for t in doc_chunk:
                text_escaped = html.escape(t.text)
                whitespace_escaped = html.escape(t.whitespace_)
                
                if t.i in tokens_to_highlight:
                    highlighted_str += f'<strong class="highlight">{text_escaped}</strong>{whitespace_escaped}'
                else:
                    highlighted_str += f"{text_escaped}{whitespace_escaped}"
            
            highlighted_contexts_map[key] = highlighted_str.replace("\n", "<br>")

        sentence_reports.append({
            'context_md': context_md,
            'context_html_plain': context_html_plain,
            'matches_map': matches_in_sentence_map, 
            'highlighted_contexts': highlighted_contexts_map,
            'timestamp': timestamp
        })
        
    return sentence_reports, global_lemmas_map, global_totals


# --- Output Writers (HTML + Markdown) ---

def write_html_reports(sentence_reports, global_lemmas_map, global_totals, output_folder, input_filename):
    """
    Writes all 5 HTML reports.
    """
    
    # 1. Write the 4 Individual Reports
    for selection_key, (_, title_plural) in POS_MAP.items():
        filename = f"{input_filename}.{title_plural.lower()}.html"
        output_path = os.path.join(output_folder, filename)
        total = global_totals[selection_key]
        lemmas_map = global_lemmas_map[selection_key] 
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(get_html_header(f"{title_plural} Analysis"))
                f.write(f"<h1>{title_plural} Analysis</h1>\n")
                f.write(f"<h2>File: <code>{input_filename}</code></h2>\n")
                
                if total == 0:
                    f.write(f"<p>No {title_plural.lower()} found in text.</p>\n")
                else:
                    f.write("<table class=\"single-report\">\n")
                    f.write("  <thead><tr><th>Context (Highlighted)</th><th>Found Lemmas</th><th>Start Time</th></tr></thead>\n")
                    f.write("  <tbody>\n")
                    for report in sentence_reports:
                        matches_for_cat = report['matches_map'][selection_key]
                        if matches_for_cat:
                            matches_cell = get_html_cell_content(matches_for_cat)
                            context_cell = report['highlighted_contexts'][selection_key]
                            
                            timestamp = report['timestamp']
                            timestamp_url = f"http://localhost:{LOCALHOST_PORT}/?time={timestamp}"
                            timestamp_cell = f'<a href="{timestamp_url}" target="_blank" title="Jump to time (localhost)">{timestamp}</a>'
                            
                            f.write(f"    <tr><td>{context_cell}</td><td>{matches_cell}</td><td>{timestamp_cell}</td></tr>\n")
                    f.write("  </tbody>\n</table>\n")

                f.write("<h3>Summary</h3>\n")
                if total == 0:
                    f.write("<p>No instances found.</p>\n")
                else:
                    f.write(f"<p>Total found: <strong>{total}</strong> instances.</p>\n")
                    f.write("<h4>Unique Lemmas List:</h4>\n<ul>\n")
                    
                    for lemma, original_texts in sorted(lemmas_map.items()):
                        display_lemma = html.escape(lemma)
                        original_word_for_url = list(original_texts)[0]
                        url_encoded_word = urllib.parse.quote_plus(original_word_for_url)
                        url = f"https://www.verbformen.es/?w={url_encoded_word}"
                        f.write(f'  <li><a href="{url}" target="_blank" title="Lookup: {original_word_for_url}"><strong>{display_lemma}</strong></a></li>\n')
                    
                    f.write("</ul>\n")
                f.write("</body>\n</html>\n")
            
            sys.stderr.write(f"-> Created '{output_path}'\n")
        except Exception as e:
            sys.stderr.write(f"\nERROR writing '{output_path}': {e}\n")

    # 2. Write the Combined Report
    filename_combined = f"{input_filename}.combined.html"
    output_path_combined = os.path.join(output_folder, filename_combined)
    try:
        with open(output_path_combined, "w", encoding="utf-8") as f:
            f.write(get_html_header("Combined Analysis"))
            f.write(f"<h1>Combined Analysis</h1>\n")
            f.write(f"<h2>File: <code>{input_filename}</code></h2>\n")
            
            if not sentence_reports:
                f.write("<p>No words found in text.</p>\n")
            else:
                f.write("<table class=\"combined\">\n")
                f.write("  <thead><tr><th>Context</th><th>Adjectives</th><th>Verbs</th><th>Nouns</th><th>Adverbs</th><th>Start Time</th></tr></thead>\n")
                f.write("  <tbody>\n")
                for report in sentence_reports:
                    timestamp = report['timestamp']
                    timestamp_url = f"http://localhost:{LOCALHOST_PORT}/?time={timestamp}"
                    timestamp_cell = f'<a href="{timestamp_url}" target="_blank" title="Jump to time (localhost)">{timestamp}</a>'
                    
                    f.write("    <tr>\n")
                    f.write(f"      <td>{report['context_html_plain']}</td>\n")
                    f.write(f"      <td>{get_html_cell_content(report['matches_map']['adj'])}</td>\n")
                    f.write(f"      <td>{get_html_cell_content(report['matches_map']['verb'])}</td>\n")
                    f.write(f"      <td>{get_html_cell_content(report['matches_map']['nom'])}</td>\n")
                    f.write(f"      <td>{get_html_cell_content(report['matches_map']['adv'])}</td>\n")
                    f.write(f"      <td>{timestamp_cell}</td>\n")
                    f.write("    </tr>\n")
                f.write("  </tbody>\n</table>\n")
            f.write("</body>\n</html>\n")
        sys.stderr.write(f"-> Created '{output_path_combined}'\n")
    except Exception as e:
        sys.stderr.write(f"\nERROR writing '{output_path_combined}': {e}\n")


def write_markdown_reports(sentence_reports, global_lemmas_map, global_totals, output_folder, input_filename):
    """
    Writes all 5 Markdown reports.
    """
    
    # 1. The 4 Individual Reports
    for selection_key, (_, title_plural) in POS_MAP.items():
        filename = f"{input_filename}.{title_plural.lower()}.md"
        output_path = os.path.join(output_folder, filename)
        total = global_totals[selection_key]
        lemmas_map = global_lemmas_map[selection_key]
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# {title_plural} Analysis\n")
                f.write(f"## File: `{input_filename}`\n\n---\n\n")
                
                if total == 0:
                    f.write(f"No {title_plural.lower()} found in text.\n")
                else:
                    f.write("| Context | Found Lemmas | Start Time |\n")
                    f.write("| :--- | :--- | :--- |\n")
                    for report in sentence_reports:
                        matches_for_cat = report['matches_map'][selection_key]
                        if matches_for_cat:
                            matches_cell = get_md_cell_content(matches_for_cat)
                            f.write(f"| {report['context_md']} | {matches_cell} | {report['timestamp']} |\n")
                
                f.write("\n\n## Summary\n")
                if total == 0:
                    f.write("No instances found.\n")
                else:
                    f.write(f"Total instances found: **{total}**\n")
                    f.write("\n**Unique Lemmas List:**\n\n")
                    for lemma in sorted(lemmas_map.keys()):
                        f.write(f"* `{lemma}`\n")
            
            sys.stderr.write(f"-> Created '{output_path}'\n")
        except Exception as e:
            sys.stderr.write(f"\nERROR writing '{output_path}': {e}\n")

    # 2. The Combined Report
    filename_combined = f"{input_filename}.combined.md"
    output_path_combined = os.path.join(output_folder, filename_combined)
    try:
        with open(output_path_combined, "w", encoding="utf-8") as f:
            f.write(f"# Combined Analysis\n")
            f.write(f"## File: `{input_filename}`\n\n---\n\n")
            
            if not sentence_reports:
                f.write("No words found in text.\n")
            else:
                f.write("| Context | Adjectives | Verbs | Nouns | Adverbs | Start Time |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
                for report in sentence_reports:
                    f.write(f"| {report['context_md']} | "
                            f"{get_md_cell_content(report['matches_map']['adj'])} | "
                            f"{get_md_cell_content(report['matches_map']['verb'])} | "
                            f"{get_md_cell_content(report['matches_map']['nom'])} | "
                            f"{get_md_cell_content(report['matches_map']['adv'])} | "
                            f"{report['timestamp']} |\n")
        
        sys.stderr.write(f"-> Created '{output_path_combined}'\n")
    except Exception as e:
        sys.stderr.write(f"\nERROR writing '{output_path_combined}': {e}\n")

# --- Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="Analyzes a German SRT file and generates 10 reports (5x HTML, 5x MD).",
        epilog="Example: python germanSrtAnalysis.py my_movie.srt"
    )
    parser.add_argument(
        'filename',
        help="The input SRT file to analyze."
    )
    
    args = parser.parse_args()
    
    # --- Path Setup ---
    input_file_path = os.path.abspath(args.filename)
    base_folder = os.path.dirname(input_file_path)
    input_filename_ext = os.path.basename(input_file_path)
    filename_no_ext = os.path.splitext(input_filename_ext)[0]
    
    output_folder = os.path.join(base_folder, "Analyse")
    
    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        sys.stderr.write(f"ERROR: Could not create output folder '{output_folder}': {e}\n")
        sys.exit(1)

    # --- Execution ---
    sys.stderr.write("Loading spaCy model 'de_core_news_lg'...\n")
    nlp = load_model()
    
    sys.stderr.write(f"Reading file: {input_filename_ext}...\n")
    raw_text = read_file(input_file_path)
    
    sys.stderr.write("Model loaded. Starting Analysis (SRT Mode)...\n")

    # Analyze
    sentence_reports, global_lemmas_map, global_totals = analyze_text_and_create_data(nlp, raw_text)

    # Write Reports
    sys.stderr.write("\nWriting HTML Reports...\n")
    write_html_reports(sentence_reports, global_lemmas_map, global_totals, output_folder, filename_no_ext)
    
    sys.stderr.write("\nWriting Markdown Reports...\n")
    write_markdown_reports(sentence_reports, global_lemmas_map, global_totals, output_folder, filename_no_ext)
    
    sys.stderr.write(f"\nSuccess! All 10 reports saved in '{output_folder}'.\n")


if __name__ == "__main__":
    main()
