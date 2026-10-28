# CVSmart — CV Classificator

CVSmart is a [Streamlit](https://streamlit.io) web app that reads a batch of CVs (PDF, DOCX, scanned PDFs via OCR), extracts candidate information, classifies each CV into one of ~50 domains / 250+ jobs, scores and ranks candidates, and exports the results to Excel and to sorted folders. It can also fetch CVs directly from an HR mailbox over IMAP.

The user interface is in French.

## Features

| Page | What it does |
|------|--------------|
| **Accueil** | Home page, shortcut to pick a CV folder |
| **Analyser** | Analyses every CV in a local folder (default: `cv_a_traiter/`) with live progress and log |
| **Emails** | Connects to an IMAP mailbox, downloads CV attachments (`.pdf`, `.docx`, `.doc`), analyses them and moves processed emails to a `CV traités` folder |
| **Résultats** | Totals, breakdown by domain, Excel export |
| **Filtrer** | Domain, minimum experience, education level, skills, free-text search (plus sex/city/age under "Plus de critères"); export or save the selection to a folder |
| **Validation** | Queue of low-confidence CVs: pick one of the model's suggested domains (with probabilities) or another one, and optionally learn from the decision |
| **Apprentissage** | Measured accuracy (overall and per domain), recent corrections, retraining |
| **Correspondance** | Paste a job offer and rank CVs against it |
| **Paramètres** | Confidence threshold, folders, session/learning reset, configured domains |

Extracted fields: name, first name, email, phone, age, sex, marital status, nationality, city, education level, school, years of experience, current position, skills, languages, certifications.

## Requirements

- **Python 3.10+** recommended, Streamlit 1.41+ (3.9 works for the app itself; `test_email.py` needs `tomli` on < 3.11, installed automatically from `requirements.txt`)
- ~2 GB of free disk space if you install the optional OCR dependency (`easyocr` pulls in PyTorch)

## Getting started

```bash
# 1. Clone your fork and enter it
git clone git@github.com:<your-user>/CV-Classificator.git
cd CV-Classificator

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

> **No OCR needed?** `easyocr` is only used for scanned CVs (PDFs with no selectable text). You can skip it to save time and disk space by installing everything except that line — the app detects that it is missing and simply skips OCR:
>
> ```bash
> grep -v '^easyocr' requirements.txt | pip install -r /dev/stdin
> ```

### Configure the mailbox (optional — only for the 📧 Emails page)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` with your IMAP server, port, address and an **app password**. This file is git-ignored: never commit it.

You can check the connection with:

```bash
python test_email.py
```

### Run the app

```bash
streamlit run app.py
```

Streamlit opens <http://localhost:8501> in your browser. On first launch the classifier is trained (a few seconds) and, if installed, the EasyOCR model is downloaded (once).

### Analyse your first CVs

1. Put your CVs (`.pdf` / `.docx`) in the `cv_a_traiter/` folder (created automatically on first launch), or type any other folder path on the **Analyser** page.
2. Click **🚀 Lancer l'analyse**.
3. Review the results in **📊 Résultats**, fix low-confidence CVs in **⚠️ Validation**, then export to Excel.

## Output folders

All created next to `app.py` and git-ignored:

| Folder | Content |
|--------|---------|
| `cv_a_traiter/` | Default input folder |
| `cv_recus_email/` | Attachments downloaded from the mailbox |
| `CV_classes/<Domaine>/…` | Copies of the CVs sorted by domain (and job, for emailed CVs) |
| `CV_filtres/` | Folders created from the **Filtrer** page |
| `exports/` | Excel exports |

`apprentissage.json` stores what the app learned from your corrections (first name → sex, etc.).

## Project structure

```
app.py                       Main Streamlit application — run this
ui.py                        Design system: colours, Lucide icons, CSS, HTML components
.streamlit/config.toml       Streamlit theme (light mode, brand colours)
gestionnaire_email.py        IMAP client: fetch CV attachments, move processed emails
CLASSEURS.py                 Older standalone version of the app (no email/validation pages), kept for reference
test_email.py                Checks the IMAP connection using .streamlit/secrets.toml
test_easyocr.py              Runs EasyOCR on the first CV of a folder: python test_easyocr.py [folder]
debug_cv.py                  Shows how name detection behaves on one PDF: python debug_cv.py file.pdf
apprentissage.json           Learned corrections
.streamlit/secrets.toml.example   Template for mailbox credentials
```

## How classification works

1. **Text extraction** — PyMuPDF for PDFs, python-docx for DOCX; if fewer than 300 characters are found, EasyOCR is used (when installed).
2. **Information extraction** — regex/heuristics in `ExtracteurInfos` (`app.py`).
3. **Classification** — first looks for known job titles in the top 15 lines of the CV, then anywhere in the text, then falls back to a TF-IDF + Naive Bayes model trained on the keywords of each domain in `CATEGORIES`.
4. **Score /100** — diploma (30) + experience (40) + profile completeness (30).
5. **Validation** — a CV goes to the Validation queue when it is unclassified, when the classification confidence is below the threshold (default 70 %) or when 2+ fields have low confidence.
6. **Learning** — every domain you validate is recorded in `apprentissage.json` (prediction vs. your choice, used for the accuracy figures). With "Apprendre de cette décision" checked, the CV text is also added to the training data and the model is retrained (automatically if "Apprentissage automatique" is on, or with "Relancer l'apprentissage"). A CV nearly identical to one you already validated gets your domain directly.

To add or tune domains and jobs, edit the `CATEGORIES` dictionary at the top of `app.py`.

## Troubleshooting

- **`❌ Impossible de lire les identifiants`** on the Emails page → `.streamlit/secrets.toml` is missing or incomplete (see above).
- **Scanned CVs come back empty** → `easyocr` is not installed; run `pip install easyocr`.
- **`.doc` files** (old Word format) are not supported for text extraction; convert them to `.docx` or PDF.
- **Slow first run** → EasyOCR downloads its models once; later runs are faster.
