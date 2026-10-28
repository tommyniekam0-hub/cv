# ============================================================
# CVSmart V9 - Version FINALE (Partie 1/2)
# ============================================================

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import fitz
import docx
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="CVSmart - L'intelligence qui trie vos talents",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CATEGORIES = {
    'Informatique': {
        'emoji': '💻', 'couleur': '#0066FF',
        'mots_cles': [
            'python', 'java', 'javascript', 'sql', 'html', 'css', 'php', 'react',
            'développeur', 'programmation', 'logiciel', 'application', 'web',
            'backend', 'frontend', 'full stack', 'mobile', 'api', 'rest',
            'docker', 'kubernetes', 'cloud', 'aws', 'azure', 'linux', 'git',
            'agile', 'scrum', 'machine learning', 'data', 'node', 'typescript',
            'informatique', 'réseau', 'système', 'devops', 'cybersécurité'
        ]
    },
    'Comptabilité': {
        'emoji': '💰', 'couleur': '#00B86B',
        'mots_cles': [
            'comptabilité', 'audit', 'bilan', 'compte', 'excel',
            'analyse financière', 'gestion financière', 'sap', 'erp',
            'comptable', 'contrôle de gestion', 'fiscalité', 'trésorerie',
            'investissement', 'budget', 'prévisionnel', 'consolidation',
            'sage', 'comptabilité générale', 'grand livre'
        ]
    },
    'Ressources Humaines': {
        'emoji': '👥', 'couleur': '#8B00FF',
        'mots_cles': [
            'rh', 'ressources humaines', 'recrutement', 'formation', 'talent',
            'gestion du personnel', 'paie', 'évaluation', 'acquisition',
            'droit du travail', 'social', 'carrière', 'onboarding', 'sirh',
            'gestion des conflits', 'entretien annuel'
        ]
    },
    'Marketing': {
        'emoji': '📢', 'couleur': '#FF6B00',
        'mots_cles': [
            'marketing', 'communication', 'digital', 'social media', 'réseaux sociaux',
            'publicité', 'brand', 'stratégie', 'content', 'seo', 'sem',
            'community manager', 'campagne', 'créatif', 'storytelling',
            'relation presse', 'growth hacking', 'analytics', 'branding',
            'brand management'
        ]
    },
    'Finance': {
        'emoji': '💵', 'couleur': '#00C4CC',
        'mots_cles': [
            'finance', 'banque', 'assurance', 'investissement', 'portefeuille',
            'trading', 'marché financier', 'risk management', 'analyse risque',
            'audit financier', 'contrôle financier', 'trésorerie', 'credit',
            'microfinance', 'gestion actif', 'ifrs', 'bâle'
        ]
    },
    'Commercial': {
        'emoji': '🤝', 'couleur': '#FF0055',
        'mots_cles': [
            'vente', 'commerce', 'négociation', 'client', 'prospection',
            'business development', 'account manager', 'sales', 'commercial',
            'relation client', 'crm', 'key account', 'objectifs',
            'force de vente', 'grands comptes'
        ]
    },
    'Non classé': {'emoji': '❓', 'couleur': '#888888', 'mots_cles': []}
}

DOSSIER_TRI = "CV_classes"
DOSSIER_EXCEL = "exports"
DOSSIER_FILTRES = "CV_filtres"
for d in [DOSSIER_TRI, DOSSIER_EXCEL, DOSSIER_FILTRES]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# CSS
# ============================================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #e0f7ff 50%, #f0fff4 100%);
    }
    
    .main .block-container {
        max-width: 1500px !important;
        padding-top: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #0a1f44;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .main-subtitle {
        color: #2d4a7c;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    
    .cvsmart-header {
        background: linear-gradient(135deg, #0066FF 0%, #00B86B 100%);
        border-radius: 14px;
        padding: 1.2rem 1.8rem;
        box-shadow: 0 8px 24px rgba(0,102,255,0.25);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .cvsmart-logo-text {
        font-size: 1.8rem;
        font-weight: 900;
        color: white;
        letter-spacing: -0.5px;
    }
    .cvsmart-logo-sub {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.95);
        font-weight: 500;
    }
    
    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 0.7rem 1.5rem;
        transition: all 0.2s ease;
        border: 2px solid transparent;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0088FF 100%);
        color: white !important;
        box-shadow: 0 4px 14px rgba(0,102,255,0.4);
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,102,255,0.5);
    }
    .stButton > button[kind="secondary"] {
        background: white;
        color: #0066FF !important;
        border: 2px solid #0066FF;
        font-weight: 700;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #0066FF;
        color: white !important;
    }
    
    .stat-card {
        background: white;
        border-radius: 14px;
        padding: 1.3rem;
        border: 2px solid #e0e7ff;
        box-shadow: 0 4px 14px rgba(0,102,255,0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,102,255,0.15);
        border-color: #0066FF;
    }
    .stat-label {
        color: #1a3a6b;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 900;
        color: #0a1f44;
        line-height: 1;
    }
    .stat-icon { font-size: 2.2rem; }
    
    .cat-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        border-left: 6px solid #0066FF;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
        gap: 0.9rem;
        margin-bottom: 0.75rem;
    }
    .cat-emoji { font-size: 2rem; }
    .cat-name {
        font-weight: 800;
        color: #0a1f44;
        font-size: 1rem;
    }
    .cat-count {
        color: #2d4a7c;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .skill-tag {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        margin: 0.25rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #0066FF 0%, #0088FF 100%);
        color: white;
        font-size: 0.85rem;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(0,102,255,0.3);
    }
    
    .badge-cat {
        display: inline-block;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.9rem;
        color: white;
    }
    
    .badge-ras {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        background: #f0f0f0;
        color: #888;
        font-size: 0.85rem;
        font-weight: 600;
        font-style: italic;
    }
    
    .step-box {
        text-align: center;
        padding: 1.2rem 0.8rem;
        background: white;
        border-radius: 12px;
        border: 2px solid #e0e7ff;
        box-shadow: 0 4px 12px rgba(0,102,255,0.08);
    }
    .step-icon { font-size: 2.2rem; margin-bottom: 0.5rem; }
    .step-title {
        font-weight: 800;
        color: #0a1f44;
        font-size: 0.9rem;
    }
    .step-desc {
        color: #4a6fa5;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0066FF, #00B86B);
    }
    
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        border-radius: 12px;
        padding: 0.5rem;
        border: 2px solid #e0e7ff;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 700;
        color: #2d4a7c;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0066FF 0%, #0088FF 100%) !important;
        color: white !important;
    }
    
    p, div, span, label { color: #0a1f44; }
    
    /* INPUTS - Texte VISIBLE */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important;
        color: #0a1f44 !important;
        border: 2px solid #c7d7f0 !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 0.8rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 3px rgba(0,102,255,0.15) !important;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    
    textarea {
        background-color: white !important;
        color: #0a1f44 !important;
    }
    
    .stTextInput > label,
    .stTextArea > label {
        color: #0a1f44 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #0a1f44 !important;
        font-weight: 900 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #2d4a7c !important;
        font-weight: 700 !important;
    }
    
    .stAlert {
        border-radius: 12px;
        font-weight: 600;
    }
    
    .filter-container {
        background: white;
        border-radius: 14px;
        padding: 1.2rem;
        border: 2px solid #e0e7ff;
        box-shadow: 0 4px 14px rgba(0,102,255,0.08);
    }
    
    .filter-header {
        font-size: 1rem;
        font-weight: 800;
        color: #0a1f44;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e7ff;
        margin-bottom: 1rem;
    }
    
    .filter-group {
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .filter-group-title {
        font-size: 0.85rem;
        font-weight: 800;
        color: #1a3a6b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .result-item {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        border: 2px solid #e0e7ff;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
    }
    .result-item:hover {
        border-color: #0066FF;
        box-shadow: 0 6px 20px rgba(0,102,255,0.15);
    }
    
    .stMultiSelect > div > div {
        background: white !important;
        border: 2px solid #c7d7f0 !important;
        border-radius: 10px !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, #0066FF 0%, #0088FF 100%) !important;
        color: white !important;
    }
    
    .stSlider > div > div > div > div {
        background: #0066FF !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# EXTRACTEUR D'INFORMATIONS
# ============================================================
class ExtracteurInfos:
    PRENOMS_FEMININS = {
        'marie', 'sophie', 'julie', 'claire', 'lucie', 'camille',
        'léa', 'chloé', 'céline', 'sandrine', 'nathalie', 'isabelle',
        'caroline', 'émilie', 'fatou', 'aïssatou', 'mariama',
        'aminata', 'kadiatou', 'awa', 'grace', 'espérance',
        'bénédicte', 'charlotte', 'sylvie', 'madeleine', 'jericae',
        'jeanne', 'françoise', 'monique', 'véronique', 'patricia',
        'catherine', 'christine', 'valérie', 'séverine', 'audrey',
        'jennifer', 'jessica', 'sarah', 'laura', 'emma', 'léna',
        'juliette', 'manon', 'élise', 'élodie', 'anaïs', 'océane',
        'jerica', 'ange', 'angele', 'angèle'
    }
    
    PRENOMS_MASCULINS = {
        'jean', 'pierre', 'paul', 'jacques', 'lucas', 'hugo',
        'antoine', 'nicolas', 'sébastien', 'thomas', 'julien',
        'maxime', 'alexandre', 'guillaume', 'françois', 'philippe',
        'laurent', 'moussa', 'ibrahima', 'amadou', 'oumar',
        'abdoulaye', 'mamadou', 'samuel', 'david', 'daniel',
        'emmanuel', 'joseph', 'alphonse', 'bernard', 'charles',
        'étienne', 'franck', 'gaston', 'henri', 'jules', 'kévin',
        'léon', 'michel', 'noël', 'oscar', 'pascal', 'raymond',
        'serge', 'victor', 'richard', 'sacha', 'marc', 'luc',
        'eric', 'éric', 'patrick', 'christophe', 'olivier',
        'vincent', 'benjamin', 'adrien', 'arthur', 'louis'
    }
    
    MOTS_INTERDITS = {
        'EXPÉRIENCES', 'EXPERIENCES', 'EXPÉRIENCE', 'EXPERIENCE',
        'FORMATION', 'FORMATIONS', 'ÉDUCATION', 'EDUCATION',
        'CERTIFICATIONS', 'CERTIFICATION', 'DIPLOMES', 'DIPLÔMES',
        'COMPÉTENCES', 'COMPETENCES', 'COMPÉTENCE', 'COMPETENCE',
        'LANGUES', 'LANGUE', 'INTÉRÊTS', 'INTERETS', 'INTÉRÊT',
        'CENTRES', 'CENTRE', 'LOISIRS', 'PROFIL', 'OBJECTIF',
        'OBJECTIFS', 'CONTACT', 'CONTACTS', 'INFORMATIONS',
        'RÉFÉRENCES', 'REFERENCES', 'PROJETS', 'PROJET',
        'ÉCOLE', 'ECOLE', 'ÉCOLES', 'UNIVERSITÉ', 'UNIVERSITE',
        'LYCÉE', 'LYCEE', 'COLLÈGE', 'COLLEGE', 'INSTITUT',
        'ENTREPRISE', 'ENTREPRISES', 'SOCIÉTÉ', 'SOCIETE',
        'STAGE', 'STAGES', 'EMPLOI', 'EMPLOIS', 'POSTE', 'POSTES',
        'RESPONSABILITÉS', 'ACTIVITÉS', 'ACTIVITES', 'MISSIONS',
        'CV', 'CURRICULUM', 'VITAE', 'RESUME', 'RÉSUMÉ',
        'NOM', 'PRENOM', 'PRÉNOM', 'NOMS', 'PRENOMS',
        'TEL', 'TÉL', 'TELEPHONE', 'TÉLÉPHONE', 'MOBILE',
        'EMAIL', 'MAIL', 'ADRESSE', 'VILLE', 'PAYS',
        'JANVIER', 'FÉVRIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI',
        'JUIN', 'JUILLET', 'AOÛT', 'AOUT', 'SEPTEMBRE', 'OCTOBRE',
        'NOVEMBRE', 'DÉCEMBRE', 'DECEMBRE',
        'COMMUNICATION', 'INNOVATION', 'PRODUIT',
        'ANNÉE', 'ANNEE', 'PREMIÈRE', 'DEUXIÈME', 'TROISIÈME',
        'TCF', 'TOEIC', 'TOEFL', 'MARKETING', 'DIGITAL'
    }
    
    def __init__(self):
        self.villes = [
            'yaoundé', 'yaounde', 'douala', 'bafoussam', 'garoua', 'bamenda',
            'maroua', 'ngaoundéré', 'ngaoundere', 'bertoua', 'ebolowa',
            'kribi', 'limbe', 'buea', 'kumba', 'edea', 'dschang', 'foumban',
            'paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes',
            'abidjan', 'dakar', 'lomé', 'lome', 'cotonou', 'libreville',
            'brazzaville', 'kinshasa', 'casablanca', 'tunis', 'londres',
            'montréal', 'montreal', 'bruxelles'
        ]
    
    def extraire_email(self, texte):
        patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}',
        ]
        for p in patterns:
            m = re.search(p, texte, re.IGNORECASE)
            if m:
                return re.sub(r'\s+', '', m.group(0)).lower()
        for tld in ['com', 'fr', 'net', 'org', 'edu', 'cm', 'uk', 'de', 'ca']:
            pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+' + tld + r'\b'
            m = re.search(pattern, texte, re.IGNORECASE)
            if m:
                email = m.group(0)
                return (email[:-len(tld)] + '.' + tld).lower()
        return "RAS"
    
    def extraire_tel(self, texte):
        patterns = [
            r'\+237[\s.-]?\d[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
            r'00237[\s.-]?\d[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
            r'\b6[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b',
            r'0[1-9][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
            r'\+33[\s.-]?\d[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
            r'\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}',
            r'\b\d{8,15}\b',
        ]
        for p in patterns:
            for m in re.findall(p, texte):
                tel = re.sub(r'[^\d+]', '', m)
                chiffres = re.sub(r'\D', '', tel)
                if len(chiffres) == 9 and chiffres.startswith('6'):
                    return f"+237 {chiffres[0]} {chiffres[1:3]} {chiffres[3:5]} {chiffres[5:7]} {chiffres[7:9]}"
                if 8 <= len(chiffres) <= 15:
                    return tel
        return "RAS"
    
    def extraire_nom_prenom(self, texte, email="RAS"):
        nom, prenom = "", ""
        
        for p in [
            r'(?:^|\n)\s*NOM\s*(?:DE\s*FAMILLE)?\s*[:\-]\s*([A-ZÀ-Ý][a-zà-ÿA-ZÀ-Ý\s\-]{1,30})',
            r'(?:^|\n)\s*Nom\s*(?:de\s*famille)?\s*[:\-]\s*([A-ZÀ-Ý][a-zà-ÿA-ZÀ-Ý\s\-]{1,30})',
        ]:
            m = re.search(p, texte, re.MULTILINE)
            if m:
                nom = m.group(1).strip().split()[0]
                break
        for p in [
            r'(?:^|\n)\s*PR[EÉ]NOM[S]?\s*[:\-]\s*([A-ZÀ-Ý][a-zà-ÿA-ZÀ-Ý\s\-]{1,30})',
            r'(?:^|\n)\s*Pr[ée]nom[s]?\s*[:\-]\s*([A-ZÀ-Ý][a-zà-ÿA-ZÀ-Ý\s\-]{1,30})',
        ]:
            m = re.search(p, texte, re.MULTILINE)
            if m:
                prenom = m.group(1).strip().split()[0]
                break
        
        if nom and prenom:
            return nom, prenom
        
        lignes = [l.strip() for l in texte.split('\n') if l.strip()]
        for ligne in lignes[:3]:
            ligne_clean = re.sub(r'[·•\-/–—|]', ' ', ligne)
            ligne_clean = re.sub(r'\s+', ' ', ligne_clean).strip()
            if len(ligne_clean) < 4 or len(ligne_clean) > 45:
                continue
            mots = re.findall(r'\b[A-Za-zÀ-ÿ]{2,20}\b', ligne_clean)
            if not (2 <= len(mots) <= 3):
                continue
            if any(m.upper() in self.MOTS_INTERDITS for m in mots):
                continue
            if not all(m[0].isupper() for m in mots):
                continue
            
            if len(mots) == 2:
                prenom = mots[0].capitalize()
                nom = mots[1].upper()
            elif len(mots) == 3:
                if mots[0].isupper() and mots[1].isupper() and mots[2].isupper():
                    nom = mots[0].upper()
                    prenom = f"{mots[1].capitalize()} {mots[2].capitalize()}"
                else:
                    prenom = f"{mots[0].capitalize()} {mots[1].capitalize()}"
                    nom = mots[2].upper()
            return nom, prenom
        
        if email and email != "RAS" and '@' in email:
            partie = re.sub(r'\d+', '', email.split('@')[0])
            for sep in ['.', '_', '-']:
                if sep in partie:
                    parts = [p for p in partie.split(sep) if p and p.upper() not in self.MOTS_INTERDITS and len(p) > 1]
                    if len(parts) >= 2:
                        return parts[1].upper(), parts[0].capitalize()
        
        return "RAS", "RAS"
    
    def extraire_niveau(self, texte):
        t = texte.lower()
        meilleur, pts = "RAS", 0
        for m in re.finditer(r'\bbac\s*\+\s*(\d+)\b', t):
            n = int(m.group(1))
            if n >= 8: niveau, p = 'Doctorat', 30
            elif n >= 5: niveau, p = 'Master/Ingénieur', 25
            elif n >= 3: niveau, p = 'Licence', 15
            elif n >= 2: niveau, p = 'BTS/DUT', 10
            else: niveau, p = 'Bac', 8
            if p > pts: pts, meilleur = p, niveau
        
        patterns = {
            r'\b(doctorat|phd|thèse|these)\b': ('Doctorat', 30),
            r'\b(master|mastère|msc|mba|dess|dea|ingénieur)\b': ('Master/Ingénieur', 25),
            r'\b(licence|bachelor|licencié)\b': ('Licence', 15),
            r'\b(bts|dut|deug|hnd)\b': ('BTS/DUT', 10),
            r'\b(baccalauréat|bac|gce)\b': ('Bac', 8),
        }
        for p, (niv, points) in patterns.items():
            if re.search(p, t, re.IGNORECASE) and points > pts:
                pts, meilleur = points, niv
        return meilleur, pts
    
    def extraire_experience(self, texte):
        candidats = []
        annee = datetime.now().year
        for p in [
            r'(\d{1,2})\s*(?:ans?|années?)\s*(?:d\'?\s*)?expérience',
            r'expérience\s*(?:de|d\')\s*(\d{1,2})\s*(?:ans?|années?)',
        ]:
            for m in re.finditer(p, texte, re.IGNORECASE):
                try:
                    v = int(m.group(1))
                    if 0 <= v <= 50: candidats.append(v)
                except: pass
        for debut, fin in re.findall(r'(19\d{2}|20\d{2})\s*[-–—à]+\s*(19\d{2}|20\d{2}|aujourd\'hui|présent)', texte, re.IGNORECASE):
            try:
                d = int(debut)
                f = annee if fin.lower() in ["aujourd'hui", 'présent'] else int(fin)
                if 1950 <= d <= f <= annee + 1:
                    candidats.append(min(f - d, 50))
            except: pass
        if not candidats: return 0
        candidats = [c for c in candidats if 0 <= c <= 50]
        return int(np.median(candidats)) if candidats else 0
    
    def extraire_age(self, texte):
        annee_actuelle = datetime.now().year
        ages = []
        for m in re.finditer(r'(\d{1,2})\s*ans\b', texte, re.IGNORECASE):
            try:
                age = int(m.group(1))
                if 16 <= age <= 80: ages.append(age)
            except: pass
        for m in re.finditer(r'(?:n[ée]e?\s*(?:le|en)?\s*)(\d{4})', texte, re.IGNORECASE):
            try:
                age = annee_actuelle - int(m.group(1))
                if 16 <= age <= 80: ages.append(age)
            except: pass
        return str(int(np.median(ages))) if ages else "RAS"
    
    def extraire_sexe(self, texte, prenom="RAS"):
        t = texte.lower()
        if re.search(r'\b(madame|mme|mlle|mademoiselle)\b', t): return "Femme"
        if re.search(r'\b(monsieur|mr)\b', t): return "Homme"
        if prenom and prenom != "RAS":
            for p in prenom.lower().split():
                if p in self.PRENOMS_FEMININS: return "Femme"
                if p in self.PRENOMS_MASCULINS: return "Homme"
        return "RAS"
    
    def extraire_situation(self, texte):
        t = texte.lower()
        if re.search(r'\b(mari[ée]e?|mariage|époux|épouse)\b', t): return "Marié(e)"
        if re.search(r'\b(c[ée]libataire|c[ée]libat)\b', t): return "Célibataire"
        if re.search(r'\b(divorc[ée]e?)\b', t): return "Divorcé(e)"
        if re.search(r'\b(veuf|veuve)\b', t): return "Veuf(ve)"
        return "RAS"
    
    def extraire_nationalite(self, texte):
        t = texte.lower()
        pays = [
            ('camerounais', 'Camerounaise'), ('camerounaise', 'Camerounaise'),
            ('cameroun', 'Camerounaise'),
            ('français', 'Française'), ('française', 'Française'),
            ('sénégalais', 'Sénégalaise'), ('sénégalaise', 'Sénégalaise'),
            ('ivoirien', 'Ivoirienne'), ('ivoirienne', 'Ivoirienne'),
            ('gabonais', 'Gabonaise'), ('gabonaise', 'Gabonaise'),
            ('congolais', 'Congolaise'), ('congolaise', 'Congolaise'),
            ('tchadien', 'Tchadienne'), ('tchadienne', 'Tchadienne'),
        ]
        for cle, val in pays:
            if re.search(r'\b' + re.escape(cle) + r'\b', t):
                return val
        return "RAS"
    
    def extraire_langues(self, texte):
        t = texte.lower()
        trouvees = []
        langues = [
            ('français', 'Français'), ('francais', 'Français'), ('french', 'Français'),
            ('anglais', 'Anglais'), ('english', 'Anglais'),
            ('espagnol', 'Espagnol'), ('spanish', 'Espagnol'),
            ('allemand', 'Allemand'), ('german', 'Allemand'),
            ('italien', 'Italien'), ('chinois', 'Chinois'),
            ('arabe', 'Arabe'), ('portugais', 'Portugais'), ('russe', 'Russe'),
        ]
        for cle, nom in langues:
            if re.search(r'\b' + re.escape(cle) + r'\b', t):
                if nom not in trouvees: trouvees.append(nom)
        return ', '.join(trouvees) if trouvees else "RAS"
    
    def extraire_competences(self, texte):
        t = texte.lower()
        trouvees = set()
        for data in CATEGORIES.values():
            for mot in data.get('mots_cles', []):
                if re.search(r'\b' + re.escape(mot) + r'\b', t):
                    trouvees.add(mot.capitalize())
        return sorted(trouvees)[:20]
    
    def extraire_certifications(self, texte):
        t = texte.lower()
        trouvees = []
        certifs = [
            'pmp', 'prince2', 'itil', 'scrum master', 'safe',
            'aws', 'azure', 'google cloud', 'cisco', 'ccna', 'ccnp',
            'microsoft', 'oracle', 'sap', 'comptia', 'ceh',
            'google analytics', 'google ads', 'google digital',
            'hubspot', 'toeic', 'toefl', 'ielts', 'tcf', 'delf', 'dalf',
            'cpa', 'acca', 'cfa', 'cia', 'cisa', 'excel'
        ]
        for c in certifs:
            if re.search(r'\b' + re.escape(c) + r'\b', t):
                trouvees.append(c.upper())
        return ', '.join(trouvees) if trouvees else "RAS"
    
    def extraire_etablissement(self, texte):
        etabs = []
        patterns = [
            r'universit[ée]\s+(?:de\s+|d\')?[A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)?',
            r'[ée]cole\s+(?:de\s+|des\s+|nationale\s+|sup[ée]rieure\s+)?[A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)?',
            r'institut\s+[A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ]+)?',
            r'[A-ZÀ-Ý][a-zà-ÿ]+\s+College',
            r'Digital\s+College',
        ]
        for p in patterns:
            for m in re.finditer(p, texte):
                etab = m.group(0).strip()
                if etab not in etabs and 5 < len(etab) < 60:
                    etabs.append(etab)
        return ', '.join(etabs[:3]) if etabs else "RAS"
    
    def extraire_poste_actuel(self, texte):
        t = texte.lower()
        postes = [
            'directeur', 'directrice', 'manager', 'responsable',
            'chef de projet', 'chef de service', 'chef d\'équipe',
            'ingénieur', 'consultant', 'consultante', 'analyste',
            'assistant', 'assistante', 'technicien', 'technicienne',
            'comptable', 'développeur', 'développeuse',
            'commercial', 'commerciale', 'secrétaire',
            'coordinateur', 'coordinatrice', 'stagiaire'
        ]
        for poste in postes:
            if re.search(r'\b' + re.escape(poste) + r'\b', t):
                return poste.capitalize()
        return "RAS"
    
    def extraire_ville(self, texte):
        t = texte.lower()
        for v in self.villes:
            if re.search(r'\b' + re.escape(v) + r'\b', t):
                return v.capitalize()
        return "RAS"
    
    def extraire_tout(self, texte):
        email = self.extraire_email(texte)
        nom, prenom = self.extraire_nom_prenom(texte, email)
        niveau, pts = self.extraire_niveau(texte)
        
        return {
            'nom': nom or "RAS",
            'prenom': prenom or "RAS",
            'email': email,
            'telephone': self.extraire_tel(texte),
            'age': self.extraire_age(texte),
            'sexe': self.extraire_sexe(texte, prenom),
            'situation': self.extraire_situation(texte),
            'nationalite': self.extraire_nationalite(texte),
            'niveau_etudes': niveau,
            'points_niveau': pts,
            'etablissement': self.extraire_etablissement(texte),
            'annees_experience': self.extraire_experience(texte),
            'poste_actuel': self.extraire_poste_actuel(texte),
            'competences': self.extraire_competences(texte),
            'langues': self.extraire_langues(texte),
            'certifications': self.extraire_certifications(texte),
            'ville': self.extraire_ville(texte),
            'texte_brut': texte
        }


def generer_resume(infos, categorie):
    nom = f"{infos.get('prenom', '')} {infos.get('nom', '')}".strip()
    if nom in ["RAS RAS", "RAS", ""]: nom = "Ce candidat"
    
    niveau = infos.get('niveau_etudes', 'RAS')
    exp = infos.get('annees_experience', 0)
    comps = infos.get('competences', [])[:5]
    ville = infos.get('ville', 'RAS')
    
    p1 = f"{nom}"
    if niveau != "RAS": p1 += f", titulaire d'un {niveau}"
    if ville != "RAS": p1 += f", basé à {ville}"
    p1 += "."
    
    if exp > 0:
        p2 = f"Possède {exp} an{'s' if exp > 1 else ''} d'expérience"
        if categorie and categorie != 'Non classé':
            p2 += f" dans le domaine {categorie.lower()}"
        p2 += "."
    else:
        p2 = "Profil débutant, prêt à s'investir."
    
    p3 = f"Compétences clés : {', '.join(comps[:4])}." if comps else ""
    return f"{p1} {p2} {p3}".strip()


class Classificateur:
    def __init__(self):
        self.pipeline = None
    
    def entrainer(self):
        textes, labels = [], []
        for cat, data in CATEGORIES.items():
            if cat == 'Non classé': continue
            for mot in data['mots_cles']:
                textes.append(f"expérience {mot} compétences {mot} maîtrise {mot}")
                textes.append(f"spécialiste {mot} expert {mot}")
                textes.append(f"projet {mot} développement {mot}")
                labels.extend([cat, cat, cat])
        
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=10000, stop_words=None,
                                      ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ('clf', MultinomialNB(alpha=0.05))
        ])
        self.pipeline.fit(textes, labels)
    
    def classifier(self, texte):
        if not self.pipeline: self.entrainer()
        t = re.sub(r'\s+', ' ', texte.lower())
        if len(t) < 20: return 'Non classé', 0.0
        try:
            pred = self.pipeline.predict([t])[0]
            proba = max(self.pipeline.predict_proba([t])[0])
            if proba < 0.2: return 'Non classé', proba
            return pred, proba
        except:
            return 'Non classé', 0.0


def calculer_score(infos):
    pts_dip = min(infos.get('points_niveau', 0), 30)
    exp = infos.get('annees_experience', 0)
    if exp >= 10: pts_exp = 40
    elif exp >= 7: pts_exp = 35
    elif exp >= 5: pts_exp = 30
    elif exp >= 3: pts_exp = 22
    elif exp >= 2: pts_exp = 15
    elif exp >= 1: pts_exp = 8
    else: pts_exp = 0
    
    pts_comp = 0
    if infos.get('nom') and infos.get('nom') != "RAS": pts_comp += 3
    if infos.get('prenom') and infos.get('prenom') != "RAS": pts_comp += 3
    if infos.get('email') and infos.get('email') != "RAS": pts_comp += 8
    if infos.get('telephone') and infos.get('telephone') != "RAS": pts_comp += 8
    if infos.get('competences') and len(infos['competences']) >= 3: pts_comp += 4
    elif infos.get('competences'): pts_comp += 2
    if infos.get('ville') and infos.get('ville') != "RAS": pts_comp += 4
    pts_comp = min(pts_comp, 30)
    
    return {'total': pts_dip + pts_exp + pts_comp,
            'diplome': pts_dip, 'experience': pts_exp, 'completude': pts_comp}


def est_cv_image(chemin):
    try:
        if not chemin.lower().endswith('.pdf'): return False
        doc = fitz.open(chemin)
        texte_total = ""
        for page in doc: texte_total += page.get_text()
        doc.close()
        return len(texte_total.strip()) < 200
    except:
        return False


def lire_avec_easyocr(chemin):
    reader = st.session_state.get('easyocr_reader')
    if not reader: return ""
    try:
        if chemin.lower().endswith('.pdf'):
            doc = fitz.open(chemin)
            texte_final = ""
            for page in doc:
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                resultats = reader.readtext(img_bytes, detail=0, paragraph=False)
                texte_final += "\n".join(resultats) + "\n"
            doc.close()
            return texte_final
        else:
            resultats = reader.readtext(chemin, detail=0, paragraph=False)
            return "\n".join(resultats)
    except Exception as e:
        print(f"Erreur EasyOCR: {e}")
        return ""


def lire_cv(chemin):
    texte = ""
    try:
        if chemin.lower().endswith('.pdf'):
            doc = fitz.open(chemin)
            for page in doc: texte += page.get_text() + "\n"
            doc.close()
        elif chemin.lower().endswith('.docx'):
            d = docx.Document(chemin)
            texte = "\n".join(p.text for p in d.paragraphs)
            for tab in d.tables:
                for r in tab.rows:
                    for c in r.cells: texte += " " + c.text
            return texte
    except Exception as e:
        print(f"Erreur PyMuPDF : {e}")
    
    if len(texte.strip()) < 200 or est_cv_image(chemin):
        texte_ocr = lire_avec_easyocr(chemin)
        if texte_ocr and len(texte_ocr.strip()) > len(texte.strip()):
            return texte_ocr
    return texte


def exporter_excel(resultats, nom_fichier=None):
    if not resultats: return None
    data = []
    for r in resultats:
        if not r.get('succes'): continue
        i = r['infos']
        s = r['scores']
        data.append({
            'Nom': i.get('nom', 'RAS'),
            'Prénom': i.get('prenom', 'RAS'),
            'Email': i.get('email', 'RAS'),
            'Téléphone': i.get('telephone', 'RAS'),
            'Âge': i.get('age', 'RAS'),
            'Sexe': i.get('sexe', 'RAS'),
            'Situation': i.get('situation', 'RAS'),
            'Nationalité': i.get('nationalite', 'RAS'),
            'Ville': i.get('ville', 'RAS'),
            'Niveau': i.get('niveau_etudes', 'RAS'),
            'Établissement': i.get('etablissement', 'RAS'),
            'Expérience (ans)': i.get('annees_experience', 0),
            'Poste actuel': i.get('poste_actuel', 'RAS'),
            'Compétences': ', '.join(i.get('competences', [])),
            'Langues': i.get('langues', 'RAS'),
            'Certifications': i.get('certifications', 'RAS'),
            'Catégorie': r['categorie'],
            'Confiance': f"{r['confiance']*100:.0f}%",
            'Score Total': s['total'],
            'Score Diplôme': s['diplome'],
            'Score Expérience': s['experience'],
            'Score Complétude': s['completude'],
            'Résumé': r.get('resume', '')
        })
    df = pd.DataFrame(data)
    if 'Score Total' in df.columns:
        df = df.sort_values('Score Total', ascending=False)
    df.insert(0, 'Rang', range(1, len(df) + 1))
    
    if not nom_fichier:
        nom_fichier = f"CVSmart_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    chemin = os.path.join(DOSSIER_EXCEL, nom_fichier)
    with pd.ExcelWriter(chemin, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='CV', index=False)
        ws = w.sheets['CV']
        for col in ws.columns:
            m = max(len(str(c.value)) if c.value else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(m + 2, 50)
    return chemin


def calculer_matching(infos, offre):
    offre_l = offre.lower()
    cv_l = infos.get('texte_brut', '').lower()
    mots_offre = set(re.findall(r'\b[a-zà-ÿ]{3,}\b', offre_l))
    mots_offre -= {'avec', 'pour', 'dans', 'vous', 'nous', 'les', 'des', 'une',
                   'que', 'qui', 'sur', 'est', 'sont', 'être', 'avoir', 'plus',
                   'poste', 'offre', 'emploi', 'recherche', 'profil', 'candidat'}
    mots_cv = set(re.findall(r'\b[a-zà-ÿ]{3,}\b', cv_l))
    communs = mots_offre & mots_cv
    score = (len(communs) / len(mots_offre) * 100) if mots_offre else 0
    
    m = re.search(r'(\d+)\s*(?:ans?|années?)\s*(?:d\')?expérience', offre_l)
    if m:
        exp_d = int(m.group(1))
        exp_cv = infos.get('annees_experience', 0)
        score = min(score + 10, 100) if exp_cv >= exp_d else max(score - 15, 0)
    
    return {'score': round(score, 1),
            'communs': sorted(communs)[:10],
            'manquants': sorted(mots_offre - mots_cv)[:5]}


def init_session():
    if 'classif' not in st.session_state:
        st.session_state.classif = Classificateur()
        with st.spinner("🚀 Initialisation..."):
            st.session_state.classif.entrainer()
    if 'extract' not in st.session_state:
        st.session_state.extract = ExtracteurInfos()
    if 'easyocr_reader' not in st.session_state:
        with st.spinner("🔍 Chargement OCR (2-3 min la 1ère fois)..."):
            try:
                import easyocr
                st.session_state.easyocr_reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
            except Exception as e:
                st.session_state.easyocr_reader = None
                print(f"EasyOCR non disponible : {e}")
    if 'resultats' not in st.session_state:
        st.session_state.resultats = []
    if 'page_active' not in st.session_state:
        st.session_state.page_active = "Accueil"
        # ============================================================
# MENU
# ============================================================
def afficher_menu():
    st.markdown("""
    <div class="cvsmart-header">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2.5rem;">📄</div>
            <div>
                <div class="cvsmart-logo-text">CVSmart</div>
                <div class="cvsmart-logo-sub">L'intelligence qui trie vos talents</div>
            </div>
        </div>
        <div style="color: white; font-weight: 700; font-size: 1rem;">v9.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('resultats'):
        nb_total = len(st.session_state.resultats)
        nb_ok = sum(1 for r in st.session_state.resultats if r.get('succes'))
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; gap: 1.5rem;
                    padding: 0.5rem 1rem; margin-bottom: 0.5rem;">
            <span style="color:#1a3a6b; font-size:0.95rem; font-weight:600;">
                📄 Total : <b style="color:#0066FF;">{nb_total}</b>
            </span>
            <span style="color:#1a3a6b; font-size:0.95rem; font-weight:600;">
                ✅ Classés : <b style="color:#00B86B;">{nb_ok}</b>
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    pages = [
        ("🏠  Accueil", "Accueil"),
        ("🔍  Analyser", "Analyser"),
        ("📊  Résultats", "Résultats"),
        ("🎯  Filtrer", "Filtrer"),
        ("🤝  Matching", "Matching"),
        ("⚙️  Paramètres", "Paramètres"),
    ]
    
    cols = st.columns(len(pages))
    for i, (label, page_name) in enumerate(pages):
        with cols[i]:
            is_active = st.session_state.page_active == page_name
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_name}",
                         use_container_width=True, type=btn_type):
                st.session_state.page_active = page_name
                st.rerun()
    
    st.markdown("<hr style='border:none; border-top:2px solid #e0e7ff; margin:1rem 0;'>",
                unsafe_allow_html=True)
    return st.session_state.page_active


# ============================================================
# PAGE ACCUEIL
# ============================================================
def page_accueil():
    st.markdown('<div class="main-title">Bienvenue sur CVSmart</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Classez, filtrez et exportez vos CV en quelques clics.</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0066FF 0%, #00B86B 100%);
                    border-radius: 20px; padding: 2.5rem; text-align: center;
                    box-shadow: 0 12px 32px rgba(0,102,255,0.3); margin: 1rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
            <h1 style="color: white; margin: 0; font-weight: 900; font-size: 2.5rem;">
                CVSmart
            </h1>
            <p style="color: rgba(255,255,255,0.95); margin-top: 0.5rem;
                      font-size: 1.1rem; font-weight: 600;">
                L'intelligence qui trie vos talents
            </p>
            <p style="color: rgba(255,255,255,0.85); font-size: 0.9rem; margin-top: 1rem;">
                PDF · DOCX · Scans (OCR activé)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="stat-card">
            <div>
                <div class="stat-label">⚡ Rapide</div>
                <div style="color:#1a3a6b; font-size:0.85rem; font-weight:600;">Analyse en quelques secondes</div>
            </div>
            <div class="stat-icon">⚡</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-card">
            <div>
                <div class="stat-label">🎯 Précis</div>
                <div style="color:#1a3a6b; font-size:0.85rem; font-weight:600;">Classification + Filtrage</div>
            </div>
            <div class="stat-icon">🎯</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="stat-card">
            <div>
                <div class="stat-label">✨ Complet</div>
                <div style="color:#1a3a6b; font-size:0.85rem; font-weight:600;">Export Excel + Dossiers</div>
            </div>
            <div class="stat-icon">✨</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🚀 Comment ça marche")
    
    etapes = [
        ("📂", "1. Import", "Sélection des CV"),
        ("📄", "2. Extraction", "Lecture + OCR"),
        ("🧠", "3. Analyse", "25 infos extraites"),
        ("🎯", "4. Classement", "Domaine détecté"),
        ("🔍", "5. Filtrage", "Critères multiples"),
        ("📊", "6. Export", "Dossiers + Excel")
    ]
    cols = st.columns(6)
    for col, (icon, t, d) in zip(cols, etapes):
        with col:
            st.markdown(f"""
            <div class="step-box">
                <div class="step-icon">{icon}</div>
                <div class="step-title">{t}</div>
                <div class="step-desc">{d}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PAGE ANALYSER
# ============================================================
def page_analyser():
    st.markdown('<div class="main-title">Analyse et classement des CV</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Sélectionnez un dossier contenant vos CV.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        chemin_dossier = st.text_input(
            "📁 Dossier sélectionné",
            value=os.path.abspath("cv_a_traiter"),
            key="chemin_dossier_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Changer", use_container_width=True, type="secondary", key="btn_changer")
    
    if st.session_state.resultats:
        nb_total = len(st.session_state.resultats)
        nb_ok = sum(1 for r in st.session_state.resultats if r.get('succes'))
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-label">📄 Nombre de CV</div>
                    <div class="stat-value">{nb_total}</div>
                </div>
                <div class="stat-icon">📄</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-label">⏳ En cours</div>
                    <div class="stat-value" style="color:#FF6B00;">0</div>
                </div>
                <div class="stat-icon">⏳</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-label">✅ Terminés</div>
                    <div class="stat-value" style="color:#00B86B;">{nb_ok}</div>
                </div>
                <div class="stat-icon">✅</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        lancer = st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True, key="btn_lancer")
    with c2:
        vider = st.button("🗑️ Vider la session", use_container_width=True, type="secondary", key="btn_vider")
    
    if vider:
        st.session_state.resultats = []
        st.rerun()
    
    if lancer:
        if not os.path.isdir(chemin_dossier):
            st.error(f"❌ Dossier introuvable : {chemin_dossier}")
            return
        
        fichiers = [f for f in os.listdir(chemin_dossier)
                    if f.lower().endswith(('.pdf', '.docx', '.doc'))]
        if not fichiers:
            st.warning(f"⚠️ Aucun CV dans {chemin_dossier}")
            return
        
        st.info(f"📊 {len(fichiers)} CV trouvés. Analyse en cours...")
        barre = st.progress(0)
        journal = st.empty()
        logs = []
        
        for i, nom in enumerate(fichiers):
            chemin = os.path.join(chemin_dossier, nom)
            heure = datetime.now().strftime("%H:%M:%S")
            logs.append(f"🔄 {heure} - Analyse de **{nom}**...")
            journal.markdown("  \n".join(logs[-5:]))
            
            texte = lire_cv(chemin)
            if not texte:
                st.session_state.resultats.append({
                    'fichier': nom, 'succes': False, 'erreur': 'Lecture impossible'
                })
                continue
            
            infos = st.session_state.extract.extraire_tout(texte)
            cat, conf = st.session_state.classif.classifier(texte)
            scores = calculer_score(infos)
            resume = generer_resume(infos, cat)
            
            st.session_state.resultats.append({
                'fichier': nom, 'succes': True,
                'categorie': cat, 'confiance': conf,
                'infos': infos, 'scores': scores, 'resume': resume
            })
            logs.append(f"✅ {heure} - **{nom}** → {cat}")
            
            dest = os.path.join(DOSSIER_TRI, cat.replace(" ", "_"))
            os.makedirs(dest, exist_ok=True)
            try: shutil.copy2(chemin, os.path.join(dest, nom))
            except: pass
            
            barre.progress((i + 1) / len(fichiers))
        
        journal.markdown("  \n".join(logs[-8:]))
        st.success(f"🎉 Analyse terminée ! {len(fichiers)} CV traités.")
        st.balloons()


# ============================================================
# PAGE RÉSULTATS
# ============================================================
def page_resultats():
    st.markdown('<div class="main-title">Résultats de classification</div>', unsafe_allow_html=True)
    
    if not st.session_state.resultats:
        st.info("📊 Aucun résultat. Allez dans **Analyser** pour commencer.")
        return
    
    resultats = [r for r in st.session_state.resultats if r.get('succes')]
    total = len(st.session_state.resultats)
    classes = len(resultats)
    nc = total - classes
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📄 Total des CV", total)
    with c2: st.metric("✅ Classés", classes)
    with c3: st.metric("❓ Non classés", nc)
    
    st.markdown("---")
    st.subheader("Répartition par domaine")
    
    compteur = {}
    for r in resultats:
        cat = r['categorie']
        compteur[cat] = compteur.get(cat, 0) + 1
    if nc > 0: compteur['Non classé'] = nc
    
    cols = st.columns(4)
    for i, (cat, nb) in enumerate(compteur.items()):
        with cols[i % 4]:
            data = CATEGORIES.get(cat, {'emoji': '❓', 'couleur': '#888888'})
            st.markdown(f"""
            <div class="cat-card" style="border-left-color: {data['couleur']};">
                <div class="cat-emoji">{data['emoji']}</div>
                <div>
                    <div class="cat-name">{cat}</div>
                    <div class="cat-count">{nb} CV</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    tab1, tab2 = st.tabs(["🏆 Classement", "📋 Détails"])
    
    with tab1:
        data = []
        for r in resultats:
            i = r['infos']
            data.append({
                'Rang': 0,
                'Nom': i.get('nom', 'RAS'),
                'Prénom': i.get('prenom', 'RAS'),
                'Catégorie': r['categorie'],
                'Niveau': i.get('niveau_etudes', 'RAS'),
                'Ville': i.get('ville', 'RAS'),
                'Âge': i.get('age', 'RAS'),
                'Sexe': i.get('sexe', 'RAS'),
                'Exp.': i.get('annees_experience', 0),
                'Email': i.get('email', 'RAS'),
                'Téléphone': i.get('telephone', 'RAS'),
                'Score': r['scores']['total']
            })
        if data:
            df = pd.DataFrame(data).sort_values('Score', ascending=False)
            df['Rang'] = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True, height=400)
    
    with tab2:
        for r in sorted(resultats, key=lambda x: x['scores']['total'], reverse=True):
            i = r['infos']
            nom_complet = f"{i.get('prenom', 'RAS')} {i.get('nom', 'RAS')}".strip()
            data_cat = CATEGORIES.get(r['categorie'], {'emoji': '❓', 'couleur': '#888'})
            
            with st.expander(f"{data_cat['emoji']} **{nom_complet}** — Score : {r['scores']['total']}/100"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("**📝 Résumé automatique**")
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e0f0ff 0%, #d0f0e0 100%);
                                border-left: 5px solid #0066FF;
                                padding:1rem 1.2rem; border-radius:10px; margin-bottom:1rem;
                                color:#0a1f44; font-weight:600;">
                        {r.get('resume', '')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**👤 Informations extraites**")
                    for k, v in [
                        ('Nom', i.get('nom', 'RAS')),
                        ('Prénom', i.get('prenom', 'RAS')),
                        ('Email', i.get('email', 'RAS')),
                        ('Téléphone', i.get('telephone', 'RAS')),
                        ('Âge', i.get('age', 'RAS')),
                        ('Sexe', i.get('sexe', 'RAS')),
                        ('Situation', i.get('situation', 'RAS')),
                        ('Nationalité', i.get('nationalite', 'RAS')),
                        ('Ville', i.get('ville', 'RAS')),
                        ('Niveau', i.get('niveau_etudes', 'RAS')),
                        ('Établissement', i.get('etablissement', 'RAS')),
                        ('Expérience', f"{i.get('annees_experience', 0)} ans"),
                        ('Poste actuel', i.get('poste_actuel', 'RAS')),
                        ('Langues', i.get('langues', 'RAS')),
                        ('Certifications', i.get('certifications', 'RAS')),
                    ]:
                        if v == "RAS":
                            st.markdown(f"- **{k}** : <span class='badge-ras'>RAS</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"- **{k}** : {v}")
                    
                    comps = i.get('competences', [])
                    if comps:
                        st.markdown("**🛠️ Compétences**")
                        st.markdown(" ".join([f'<span class="skill-tag">{c}</span>' for c in comps[:15]]),
                                    unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f"""
                    <div style="text-align:center; padding:1rem;">
                        <div style="color:#2d4a7c; font-weight:700; font-size:0.9rem;">Domaine détecté</div>
                        <div style="margin:0.7rem 0;">
                            <span class="badge-cat" style="background:{data_cat['couleur']};">
                                {data_cat['emoji']} {r['categorie']}
                            </span>
                        </div>
                        <div style="color:#2d4a7c; font-weight:600; font-size:0.85rem;">
                            Confiance : {r['confiance']*100:.0f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("📥 Exporter en Excel", type="primary", key="btn_export_res"):
        chemin = exporter_excel(st.session_state.resultats)
        if chemin:
            st.success(f"✅ Exporté : {chemin}")
            with open(chemin, 'rb') as f:
                st.download_button("⬇️ Télécharger", data=f,
                                   file_name=os.path.basename(chemin),
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================
# PAGE FILTRER
# ============================================================
def page_filtrer():
    st.markdown('<div class="main-title">🎯 Filtrer les CV</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Combinez les critères pour trouver les candidats idéaux.</div>', unsafe_allow_html=True)
    
    if not st.session_state.resultats:
        st.info("📊 Aucun CV analysé. Allez dans **Analyser** d'abord.")
        return
    
    resultats = [r for r in st.session_state.resultats if r.get('succes')]
    
    col_filtres, col_resultats = st.columns([1, 3])
    
    with col_filtres:
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown('<div class="filter-header">🔍 FILTRES</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">📚 Niveau d\'études</div>', unsafe_allow_html=True)
        niveaux_possibles = ['Bac', 'BTS/DUT', 'Licence', 'Master/Ingénieur', 'Doctorat']
        niveaux_counts = {n: sum(1 for r in resultats if r['infos'].get('niveau_etudes') == n) for n in niveaux_possibles}
        niveaux_selection = st.multiselect(
            "Niveau", options=niveaux_possibles,
            format_func=lambda x: f"{x} ({niveaux_counts[x]})",
            key="f_niveau", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">👤 Sexe</div>', unsafe_allow_html=True)
        sexes_possibles = ['Homme', 'Femme', 'RAS']
        sexes_counts = {s: sum(1 for r in resultats if r['infos'].get('sexe') == s) for s in sexes_possibles}
        sexes_selection = st.multiselect(
            "Sexe", options=sexes_possibles,
            format_func=lambda x: f"{x} ({sexes_counts[x]})",
            key="f_sexe", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">📍 Ville</div>', unsafe_allow_html=True)
        villes_dispo = sorted(set(r['infos'].get('ville', 'RAS') for r in resultats))
        villes_counts = {v: sum(1 for r in resultats if r['infos'].get('ville') == v) for v in villes_dispo}
        villes_selection = st.multiselect(
            "Ville", options=villes_dispo,
            format_func=lambda x: f"{x} ({villes_counts[x]})",
            key="f_ville", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">🏷️ Domaine</div>', unsafe_allow_html=True)
        cats_dispo = sorted(set(r['categorie'] for r in resultats))
        cats_counts = {c: sum(1 for r in resultats if r['categorie'] == c) for c in cats_dispo}
        cats_selection = st.multiselect(
            "Catégorie", options=cats_dispo,
            format_func=lambda x: f"{x} ({cats_counts[x]})",
            key="f_cat", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">📅 Âge</div>', unsafe_allow_html=True)
        ages_valides = [int(r['infos']['age']) for r in resultats 
                        if str(r['infos'].get('age', 'RAS')).isdigit()]
        if ages_valides:
            age_min_default, age_max_default = min(ages_valides), max(ages_valides)
        else:
            age_min_default, age_max_default = 18, 60
        age_range = st.slider("Âge", min_value=16, max_value=70,
                              value=(age_min_default, age_max_default), key="f_age")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">💼 Expérience</div>', unsafe_allow_html=True)
        exp_range = st.slider("Années d'expérience", min_value=0, max_value=40,
                              value=(0, 40), key="f_exp")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">⭐ Score minimum</div>', unsafe_allow_html=True)
        score_min = st.slider("Score", min_value=0, max_value=100, value=0, key="f_score")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">🌍 Langues</div>', unsafe_allow_html=True)
        langues_dispo = set()
        for r in resultats:
            lang = r['infos'].get('langues', 'RAS')
            if lang != 'RAS':
                for l in lang.split(', '): langues_dispo.add(l.strip())
        langues_selection = st.multiselect(
            "Langues", options=sorted(langues_dispo),
            key="f_langues", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">📜 Certifications</div>', unsafe_allow_html=True)
        certs_dispo = set()
        for r in resultats:
            cert = r['infos'].get('certifications', 'RAS')
            if cert != 'RAS':
                for c in cert.split(', '): certs_dispo.add(c.strip())
        certs_selection = st.multiselect(
            "Certifications", options=sorted(certs_dispo),
            key="f_certs", label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-group"><div class="filter-group-title">🔍 Recherche libre</div>', unsafe_allow_html=True)
        recherche = st.text_input("Recherche", placeholder="Ex: marketing, Python...",
                                  key="f_recherche", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    resultats_filtres = resultats.copy()
    
    if niveaux_selection:
        resultats_filtres = [r for r in resultats_filtres if r['infos'].get('niveau_etudes') in niveaux_selection]
    if sexes_selection:
        resultats_filtres = [r for r in resultats_filtres if r['infos'].get('sexe') in sexes_selection]
    if villes_selection:
        resultats_filtres = [r for r in resultats_filtres if r['infos'].get('ville') in villes_selection]
    if cats_selection:
        resultats_filtres = [r for r in resultats_filtres if r['categorie'] in cats_selection]
    
    resultats_filtres = [r for r in resultats_filtres 
                         if (str(r['infos'].get('age', 'RAS')).isdigit() 
                             and age_range[0] <= int(r['infos']['age']) <= age_range[1])
                         or r['infos'].get('age') == 'RAS']
    
    resultats_filtres = [r for r in resultats_filtres if exp_range[0] <= r['infos'].get('annees_experience', 0) <= exp_range[1]]
    
    if langues_selection:
        resultats_filtres = [r for r in resultats_filtres 
                             if any(l in r['infos'].get('langues', 'RAS') for l in langues_selection)]
    if certs_selection:
        resultats_filtres = [r for r in resultats_filtres 
                             if any(c in r['infos'].get('certifications', 'RAS') for c in certs_selection)]
    
    resultats_filtres = [r for r in resultats_filtres if r['scores']['total'] >= score_min]
    
    if recherche:
        rech_lower = recherche.lower()
        resultats_filtres = [r for r in resultats_filtres if rech_lower in r['infos'].get('texte_brut', '').lower()]
    
    with col_resultats:
        nb_initial = len(resultats)
        nb_filtres = len(resultats_filtres)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0066FF 0%, #00B86B 100%);
                    border-radius: 12px; padding: 1rem 1.5rem; color: white;
                    margin-bottom: 1rem; display: flex; justify-content: space-between;
                    align-items: center;">
            <div style="font-weight: 800; font-size: 1.1rem;">🎯 {nb_filtres} CV correspondent</div>
            <div style="opacity: 0.9; font-size: 0.9rem;">sur {nb_initial} CV analysés</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not resultats_filtres:
            st.warning("⚠️ Aucun CV ne correspond à ces critères.")
        else:
            for r in sorted(resultats_filtres, key=lambda x: x['scores']['total'], reverse=True):
                i = r['infos']
                nom = f"{i.get('prenom', 'RAS')} {i.get('nom', 'RAS')}".strip()
                data_cat = CATEGORIES.get(r['categorie'], {'emoji': '❓', 'couleur': '#888'})
                
                st.markdown(f"""
                <div class="result-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: 800; color: #0a1f44; font-size: 1.05rem;">
                                {nom}
                            </div>
                            <div style="color: #2d4a7c; font-size: 0.85rem; margin-top: 0.3rem;">
                                {i.get('niveau_etudes', 'RAS')} · {i.get('sexe', 'RAS')} · {i.get('age', 'RAS')} ans · 📍 {i.get('ville', 'RAS')}
                            </div>
                            <div style="color: #4a6fa5; font-size: 0.8rem; margin-top: 0.3rem;">
                                ✉️ {i.get('email', 'RAS')} · 📞 {i.get('telephone', 'RAS')}
                            </div>
                            <div style="color: #4a6fa5; font-size: 0.8rem; margin-top: 0.3rem;">
                                💼 {i.get('poste_actuel', 'RAS')} · ⏱️ {i.get('annees_experience', 0)} ans d'exp.
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span class="badge-cat" style="background: {data_cat['couleur']}; font-size: 0.75rem;">
                                {data_cat['emoji']} {r['categorie']}
                            </span>
                            <div style="font-size: 1.5rem; font-weight: 900; color: #0066FF; margin-top: 0.5rem;">
                                {r['scores']['total']}
                            </div>
                            <div style="color: #888; font-size: 0.7rem;">Score / 100</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if resultats_filtres:
            st.markdown("---")
            st.subheader("📤 Exporter la sélection")
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("📁 Créer un dossier", type="primary",
                             use_container_width=True, key="btn_export_dossier"):
                    nom_parts = []
                    if niveaux_selection: nom_parts.append("_".join(niveaux_selection).replace("/", ""))
                    if sexes_selection: nom_parts.append("_".join(sexes_selection))
                    if villes_selection: nom_parts.append("_".join(villes_selection))
                    if cats_selection: nom_parts.append("_".join(cats_selection))
                    if not nom_parts: nom_parts.append("Selection")
                    
                    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nom_dossier = "_".join(nom_parts).replace(" ", "_") + f"_{horodatage}"
                    chemin_dossier = os.path.join(DOSSIER_FILTRES, nom_dossier)
                    os.makedirs(chemin_dossier, exist_ok=True)
                    
                    for r in resultats_filtres:
                        fichier_orig = r.get('fichier', '')
                        for dossier_racine in [".", "cv_a_traiter", DOSSIER_TRI]:
                            recherche = os.path.join(dossier_racine, fichier_orig)
                            if os.path.exists(recherche):
                                shutil.copy2(recherche, os.path.join(chemin_dossier, fichier_orig))
                                break
                    
                    st.success(f"✅ Dossier créé : {chemin_dossier}")
                    st.info(f"📁 {len(resultats_filtres)} CV copiés")
            
            with col_b:
                if st.button("📥 Exporter en Excel", type="primary",
                             use_container_width=True, key="btn_export_filtre"):
                    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nom_fichier = f"Selection_{horodatage}.xlsx"
                    chemin = exporter_excel(resultats_filtres, nom_fichier)
                    if chemin:
                        st.success(f"✅ Exporté : {chemin}")
                        with open(chemin, 'rb') as f:
                            st.download_button(
                                "⬇️ Télécharger", data=f,
                                file_name=os.path.basename(chemin),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )


# ============================================================
# PAGE MATCHING
# ============================================================
def page_matching():
    st.markdown('<div class="main-title">🤝 Matching avec une offre</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Collez une offre et voyez les CV qui correspondent.</div>', unsafe_allow_html=True)
    
    offre = st.text_area(
        "📝 Description de l'offre",
        height=200,
        placeholder="Ex: Développeur Python Senior\n5 ans d'expérience minimum\nPython, Django, AWS, Docker",
        key="offre_text",
        help="Collez ici la description du poste"
    )
    
    if st.button("🎯 Lancer le matching", type="primary", key="btn_matching"):
        if not offre.strip():
            st.warning("⚠️ Collez une offre d'emploi")
            return
        if not st.session_state.resultats:
            st.warning("⚠️ Aucun CV analysé.")
            return
        
        resultats = [r for r in st.session_state.resultats if r.get('succes')]
        matchings = []
        for r in resultats:
            m = calculer_matching(r['infos'], offre)
            matchings.append({'CV': r, **m})
        matchings.sort(key=lambda x: x['score'], reverse=True)
        
        st.markdown("---")
        st.subheader("🏆 Résultats du matching")
        
        for i, m in enumerate(matchings[:10]):
            r = m['CV']
            i_info = r['infos']
            nom = f"{i_info.get('prenom', 'RAS')} {i_info.get('nom', 'RAS')}".strip()
            
            if m['score'] >= 70: badge = "✅ MATCH FORT"
            elif m['score'] >= 40: badge = "⚠️ MATCH PARTIEL"
            else: badge = "❌ FAIBLE"
            
            with st.expander(f"**{nom}** — {badge} : {m['score']}%", expanded=(i < 3)):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Score : {m['score']}%**")
                    st.progress(m['score'] / 100)
                    st.markdown(f"**Catégorie :** {r['categorie']}")
                    st.markdown(f"**Expérience :** {i_info.get('annees_experience', 0)} ans")
                with c2:
                    if m['communs']:
                        st.markdown("**✅ Points forts :**")
                        for mot in m['communs'][:6]: st.markdown(f"- {mot}")
                    if m['manquants']:
                        st.markdown("**⚠️ À améliorer :**")
                        for mot in m['manquants'][:4]: st.markdown(f"- {mot}")


# ============================================================
# PAGE PARAMÈTRES
# ============================================================
def page_parametres():
    st.markdown('<div class="main-title">⚙️ Paramètres</div>', unsafe_allow_html=True)
    st.subheader("📁 Dossiers")
    c1, c2, c3 = st.columns(3)
    with c1: st.text_input("Classement", value=DOSSIER_TRI, disabled=True, key="p_d1")
    with c2: st.text_input("Export", value=DOSSIER_EXCEL, disabled=True, key="p_d2")
    with c3: st.text_input("Filtres", value=DOSSIER_FILTRES, disabled=True, key="p_d3")
    
    st.markdown("---")
    st.subheader("🏷️ Catégories")
    for cat, data in CATEGORIES.items():
        with st.expander(f"{data['emoji']} {cat} ({len(data['mots_cles'])} mots-clés)"):
            if data['mots_cles']: st.write(", ".join(data['mots_cles']))
            else: st.write("Catégorie par défaut")
    
    st.markdown("---")
    st.subheader("ℹ️ À propos")
    st.markdown("""
    **CVSmart v9.0** — L'intelligence qui trie vos talents
    
    - 📄 Support : PDF, DOCX, Scans (OCR)
    - 🎯 7 catégories professionnelles
    - 📊 Extraction de 25 champs
    - 🔍 Filtrage multi-critères
    - 🤝 Matching avec offres
    - 📁 Export dossiers + Excel
    - ✅ "RAS" si info absente
    """)


# ============================================================
# MAIN
# ============================================================
def main():
    inject_css()
    init_session()
    page = afficher_menu()
    
    if page == "Accueil": page_accueil()
    elif page == "Analyser": page_analyser()
    elif page == "Résultats": page_resultats()
    elif page == "Filtrer": page_filtrer()
    elif page == "Matching": page_matching()
    elif page == "Paramètres": page_parametres()


if __name__ == "__main__":
    main()