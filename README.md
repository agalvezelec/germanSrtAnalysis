# German SRT Morphological Analyzer

A Natural Language Processing (NLP) tool built with Python and spaCy. This project automates the linguistic analysis of German subtitles (.srt files) to create detailed study aids for language learners.

It processes subtitle streams to extract Nouns, Verbs, Adjectives, and Adverbs, identifying their base forms (lemmas) and presenting them in rich, interactive HTML and Markdown reports.

[!] The lemmas can be wrong sometimes. You should check them with a dictionary.

#  Features

- Contextual Analysis: Analyzes words within their original sentences to preserve meaning and grammatical context.

- SRT Parsing: Custom regex logic extracts accurate start timestamps and cleans HTML tags (like <i>) from raw subtitle data.

- Dual Output System: Automatically generates an Analyse/ folder containing 10 reports per video:

- 5 HTML Reports: Interactive tables with CSS styling and context highlighting.

- 5 Markdown Reports: Clean, portable data tables for documentation.

## Interactive Learning Tools (HTML):

- Smart Linking: Words link directly to Verbformen.es for conjugation/declension. The tool smartly links the original inflected form (e.g., "ging") rather than the lemma ("gehen") for better dictionary results.

- Video Integration: Timestamps link to http://localhost:8080/?time=..., allowing integration with local video players.

Context Highlighting: Detected words are highlighted (<strong>) directly within the sentence context.

Advanced Lemmatization: * Handles German noun articles (e.g., outputs der Mann instead of just Mann).

Uses the de_core_news_lg model for vector-based accuracy on complex forms like imperatives.

#  Tech Stack

Python 3

spaCy: Industrial-strength NLP engine (using the Large German model).

Regex: For parsing non-standardized text formats (SRT).

HTML/CSS: For generating frontend reports programmatically.

📦 Installation

Prerequisites

Python 3.8+

A Linux/Unix environment (recommended).

Setup

Clone the repository:

```bash
git clone [https://github.com/yourusername/german-srt-analyzer.git](https://github.com/yourusername/german-srt-analyzer.git)
cd german-srt-analyzer
```


Create a Virtual Environment:

```
python3 -m venv .venv
```


Activate the Environment:

```
source .venv/bin/activate
```


Install Dependencies:

```
python -m pip install spacy
python -m spacy download de_core_news_lg
```


Note: The _lg (large) model is required for better accuracy with vectors and lemmatization.

# Usage

Direct Python Usage

Ensure your virtual environment is active:

source .venv/bin/activate
python germanSrtAnalysis.py /path/to/your/movie.srt


Global Command (Optional)

You can use the provided germanSrtAnalysis.sh wrapper to run the tool from anywhere without manually activating the environment every time.

Edit germanSrtAnalysis.sh and set PROJECT_DIR to your installation path.

Make it executable: chmod +x germanSrtAnalysis.sh

(Optional) Symlink it to your bin: sudo ln -s $(pwd)/germanSrtAnalysis.sh /usr/local/bin/german-analyze

## Output Structure

Running the script on Dark.S01E01.srt creates a folder Analyse/ containing:

Dark.S01E01.nomen.html / .md (Nouns with articles)

Dark.S01E01.verben.html / .md (Verbs)

Dark.S01E01.adjektive.html / .md (Adjectives)

Dark.S01E01.adverbien.html / .md (Adverbs)

Dark.S01E01.combined.html / .md (All categories in one sequential table)

## Challenges & Solutions

Most of this project and documentation was vibed coded with a LLM (Gemini 3 Pro). After a while experimenting with several spacy-based scripts I decided to unify the morphological analysis in a big script. 

I did not included prepositions and conjunctions, I think that would be an overkill for learning. A 20 minute video already generates huge tables. The cognitive load is already too high. 

In the future I would like to filter easy vocabulary that the user already knows to reduce the size of these tables. Maybe a custom database or a LLM filtering basic words will do it. 





## Key challenges solved during development:

- Markdown Table Breaking: Tables initially broke in some viewers because SRT files contain literal line breaks (\n).

- Solution: Implemented a sanitation layer that normalizes whitespace specifically for Markdown output rows.

- Lemmatization Accuracy: Imperatives (e.g., "Lass!") were difficult to lemmatize with smaller models.

- Solution: Upgraded to the de_core_news_lg model to leverage word vectors for better context understanding.

- Context vs. Clarity: Early versions grouped words but lost the sentence context.

- Solution: Refactored the logic to maintain a "sentence-first" data structure, highlighting specific words within the full sentence string for better readability.

