# ============================================================
# ui.py
# Design system CVSmart : couleurs, icônes (Lucide), CSS et petits
# composants HTML réutilisés par les pages de app.py
# ============================================================

import base64
import zlib
from html import escape

import streamlit as st

# ============================================================
# COULEURS
# ============================================================
BLEU = "#0E2A6B"
ROUGE = "#D7202B"
VERT = "#1E7A44"
GRIS = "#5B6478"

# Couleurs (fond, texte) des domaines — identiques sur toutes les pages
TONS = {
    'bleu': ("#E5ECFB", "#0E2A6B"),
    'vert': ("#DDF3E6", "#1E7A44"),
    'violet': ("#ECE5FB", "#5B2BB5"),
    'orange': ("#FCE9D9", "#9A4A0B"),
    'turquoise': ("#DDF2EE", "#11695E"),
    'rose': ("#FCE4E6", "#B3121F"),
    'ambre': ("#FCEFD6", "#8A5A00"),
    'gris': ("#ECEFF4", "#3A4357"),
}
TONS_DOMAINES = {
    'Informatique': 'bleu', 'Comptabilité': 'vert', 'Ressources Humaines': 'violet',
    'Marketing': 'orange', 'Finance': 'turquoise', 'Commercial et Vente': 'rose',
    'Non classé': 'gris',
}
_ROTATION = ['bleu', 'vert', 'violet', 'orange', 'turquoise', 'rose']


def ton_domaine(domaine):
    """Couleurs (fond, texte) stables pour un domaine"""
    ton = TONS_DOMAINES.get(domaine) or _ROTATION[zlib.crc32(domaine.encode('utf-8')) % len(_ROTATION)]
    return TONS[ton]

# ============================================================
# ICÔNES (Lucide, licence ISC — https://lucide.dev)
# ============================================================
ICONES = {
    'accueil': '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'recherche': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'fichier': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    'filtre': '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    'valide': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    'apprentissage': '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
    'correspondance': '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
    'parametres': '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
    'email': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'eclair': '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    'cible': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    'bouclier': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    'dossier': '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    'horloge': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    'alerte': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    'erreur': '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    'boite': '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    'trombone': '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
}


def _svg(nom, couleur, epaisseur=2):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
            f'stroke="{couleur}" stroke-width="{epaisseur}" stroke-linecap="round" stroke-linejoin="round">{ICONES[nom]}</svg>')


def _data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode('utf-8')).decode('ascii')


def image_svg(svg, taille, alt=""):
    """st.html supprime les <svg> inline : on les affiche en <img> data-URI"""
    return f'<img src="{_data_uri(svg)}" width="{taille}" height="{taille}" alt="{alt}" style="flex-shrink:0;display:inline-block">'


def icone(nom, taille=20, couleur=GRIS, epaisseur=2):
    """Icône Lucide (couleur explicite : currentColor n'est pas transmis à une image)"""
    return image_svg(_svg(nom, couleur, epaisseur), taille)


def _icone_masque(nom):
    """Icône en data-URI, utilisée comme masque CSS pour les boutons Streamlit"""
    return _data_uri(_svg(nom, "black"))


_LOGO_CIBLE = '''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40" fill="none">
<circle cx="11" cy="8.5" r="4.5" fill="#E3222F"/>
<path d="M6.5 34C7.5 23 13 17 21.5 15.5" stroke="#E3222F" stroke-width="5" stroke-linecap="round"/>
<path d="M20 34C21.5 26 26.5 21.5 34 20.5" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>
</svg>'''

_LOGO_CVSMART = f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="{BLEU}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round">
<path d="M38 5H13a3 3 0 0 0-3 3v48a3 3 0 0 0 3 3h20"/><path d="M38 5l12 12v14"/><path d="M38 5v12h12"/>
<circle cx="26" cy="29" r="5"/><path d="M17 45c1.5-5.5 5-8 9-8s7.5 2.5 9 8"/>
<circle cx="46" cy="49" r="11" fill="{ROUGE}" stroke="#FFFFFF" stroke-width="3"/>
<path d="m40.5 49 4 4 7-7.5" stroke="#FFFFFF" stroke-width="3.5"/>
</svg>'''
LOGO_CIBLE = image_svg(_LOGO_CIBLE, 36, "CIBLE RH")
LOGO_CVSMART = image_svg(_LOGO_CVSMART, 76, "CVSmart")

# ============================================================
# COMPOSANTS HTML
# ============================================================
def afficher(contenu):
    """Affiche un fragment HTML (sans interprétation Markdown)"""
    st.html(contenu)


def entete(titre, sous_titre=None):
    sous = f'<div class="cv-sous-titre">{escape(sous_titre)}</div>' if sous_titre else ''
    afficher(f'<div class="cv-titre">{escape(titre)}</div>{sous}')


def carte_stat(libelle, valeur, couleur=BLEU, icone_nom=None, ton=None, sous_texte=None, couleur_sous=GRIS):
    """Carte chiffre clé (Analyser, Résultats, Apprentissage)"""
    pastille = ''
    if icone_nom:
        fond, trait = TONS[ton or 'bleu']
        pastille = f'<div class="cv-stat-icone" style="background:{fond}">{icone(icone_nom, 22, trait)}</div>'
    sous = f'<div class="cv-stat-sous" style="color:{couleur_sous}">{sous_texte}</div>' if sous_texte else ''
    return (f'<div class="cv-carte cv-stat">{pastille}<div><div class="cv-stat-libelle">{escape(libelle)}</div>'
            f'<div class="cv-stat-valeur" style="color:{couleur}">{valeur}</div>{sous}</div></div>')


def grille(elements, colonnes):
    return f'<div class="cv-grille" style="grid-template-columns:repeat({colonnes},minmax(0,1fr))">{"".join(elements)}</div>'


def pastille_domaine(domaine):
    fond, texte = ton_domaine(domaine)
    return f'<span class="cv-pill" style="background:{fond};color:{texte}">{escape(domaine)}</span>'


def pastille(texte, ton='bleu'):
    fond, couleur = TONS[ton]
    return f'<span class="cv-pill" style="background:{fond};color:{couleur}">{escape(texte)}</span>'


def barre(pourcentage, couleur=BLEU):
    pourcentage = max(0, min(100, pourcentage))
    return f'<div class="cv-barre"><div style="width:{pourcentage:.0f}%;background:{couleur}"></div></div>'


def message(texte, ton='bleu', icone_nom='valide'):
    """Bandeau d'information sobre (remplace st.success/st.info à emojis)"""
    fond, couleur = TONS[ton]
    afficher(f'<div class="cv-message" style="background:{fond};color:{couleur}">'
             f'{icone(icone_nom, 18, couleur)}<span>{texte}</span></div>')

# ============================================================
# CSS
# ============================================================
# Boutons Streamlit qui portent une icône : clé du widget → icône
ICONES_BOUTONS = {
    'nav_accueil': 'accueil', 'nav_analyser': 'recherche', 'nav_emails': 'email',
    'nav_resultats': 'fichier', 'nav_filtrer': 'filtre', 'nav_validation': 'valide',
    'nav_apprentissage': 'apprentissage', 'nav_correspondance': 'correspondance',
    'nav_parametres': 'parametres', 'btn_accueil_dossier': 'dossier',
}

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, .stApp *:not([data-testid="stIconMaterial"]) {{
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}}
.stApp {{ background: #F4F7FC; color: #1F2A44; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
.block-container {{ padding: 2.4rem 3rem 3rem 3rem !important; max-width: 1180px; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0F2D74 0%, #0A1D52 100%);
    min-width: 228px !important; max-width: 228px !important;
}}
[data-testid="stSidebarHeader"], [data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
[data-testid="stSidebarContent"] {{ padding: 0 !important; }}
[data-testid="stSidebarUserContent"] {{ padding: 1.6rem 0.15rem 1rem 0.15rem !important; width: 100% !important; }}
[data-testid="stSidebarUserContent"] > div {{ width: 100% !important; }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 0.35rem; width: 100% !important; }}
[data-testid="stSidebar"] [data-testid="stElementContainer"], [class*="st-key-nav_"] .stButton {{ width: 100% !important; }}
.cv-marque {{ display: flex; align-items: center; gap: 0.6rem; padding: 0 0.5rem 1rem 0.5rem; color: #fff; }}
.cv-marque-nom {{ font-weight: 800; font-size: 1.05rem; line-height: 1.1; }}
.cv-marque-sous {{ font-size: 0.85rem; opacity: 0.9; }}
.cv-pied {{ position: fixed; bottom: 1.4rem; left: 1.3rem; color: rgba(255,255,255,0.85); font-size: 0.78rem; line-height: 1.5; }}
[class*="st-key-nav_"] button {{
    width: 100% !important; background: transparent !important; border: none !important; color: #fff !important;
    justify-content: flex-start !important; gap: 0.8rem; padding: 0.55rem 0.8rem !important;
    min-height: 2.6rem; border-radius: 8px !important; box-shadow: none !important;
}}
[class*="st-key-nav_"] button p {{ font-size: 0.98rem !important; font-weight: 500; }}
[class*="st-key-nav_"] button:hover {{ background: rgba(255,255,255,0.08) !important; }}
[class*="st-key-nav_"] button[kind="primary"],
[class*="st-key-nav_"] [data-testid="stBaseButton-primary"] {{ background: {ROUGE} !important; }}
[class*="st-key-nav_"] [data-testid="stBaseButton-primary"] p {{ font-weight: 700; }}

/* ---------- Titres & cartes ---------- */
.cv-titre {{ font-size: 1.95rem; font-weight: 800; color: {BLEU}; letter-spacing: -0.01em; line-height: 1.2; }}
.cv-sous-titre {{ color: {GRIS}; font-size: 0.98rem; margin-top: 0.3rem; }}
.cv-h2 {{ font-size: 1.15rem; font-weight: 700; color: {BLEU}; margin: 0.4rem 0 0.2rem 0; }}
.cv-h3 {{ font-size: 0.95rem; font-weight: 700; color: {BLEU}; margin-bottom: 0.4rem; }}
.cv-label {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; color: {GRIS}; text-transform: uppercase; }}
.cv-muted {{ color: {GRIS}; font-size: 0.88rem; }}
.cv-carte, [class*="st-key-carte"] {{
    background: #fff; border: 1px solid #DCE3EF; border-radius: 14px;
}}
.cv-carte {{ padding: 1.2rem 1.4rem; }}
[class*="st-key-carte"] {{ padding: 1.3rem 1.4rem; }}
.cv-grille {{ display: grid; gap: 1.2rem; }}
.cv-stat {{ display: flex; align-items: center; gap: 1.1rem; }}
.cv-stat-icone {{ width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }}
.cv-stat-libelle {{ color: {GRIS}; font-size: 0.92rem; }}
.cv-stat-valeur {{ font-size: 2.1rem; font-weight: 800; line-height: 1.15; }}
.cv-stat-sous {{ font-size: 0.85rem; font-weight: 600; margin-top: 0.15rem; }}
.cv-pill {{ display: inline-block; padding: 0.22rem 0.75rem; border-radius: 999px; font-size: 0.82rem; font-weight: 600; white-space: nowrap; }}
.cv-barre {{ height: 10px; background: #E4EAF6; border-radius: 999px; overflow: hidden; }}
.cv-barre > div {{ height: 100%; border-radius: 999px; }}
.cv-message {{ display: flex; align-items: center; gap: 0.6rem; padding: 0.8rem 1rem; border-radius: 10px; font-size: 0.92rem; font-weight: 500; }}

/* ---------- Boutons ---------- */
.stButton button p, .stDownloadButton button p {{ white-space: nowrap; }}
.stButton button, .stDownloadButton button {{ border-radius: 8px !important; font-weight: 600 !important; min-height: 2.9rem; padding: 0.5rem 1.4rem !important; }}
[data-testid="stBaseButton-primary"] {{ background: {ROUGE} !important; border: 1px solid {ROUGE} !important; color: #fff !important; }}
[data-testid="stBaseButton-primary"]:hover {{ background: #B81A24 !important; border-color: #B81A24 !important; }}
[data-testid="stBaseButton-secondary"] {{ background: #fff !important; border: 1.5px solid {BLEU} !important; color: {BLEU} !important; }}
[data-testid="stBaseButton-secondary"]:hover {{ background: #EEF2FA !important; }}
[data-testid="stBaseButton-tertiary"] {{ color: {BLEU} !important; text-decoration: underline; min-height: 0 !important; padding: 0 !important; }}
[data-testid="stBaseButton-tertiary"] p {{ font-weight: 700; }}
.st-key-btn_ouvrir_validation button {{ background: {BLEU} !important; border-color: {BLEU} !important; }}
.st-key-btn_ouvrir_validation button:hover {{ background: #0A1F52 !important; }}
{''.join(f'.st-key-{cle} button::before {{ content: ""; width: 20px; height: 20px; flex-shrink: 0; background-color: currentColor; -webkit-mask: url({_icone_masque(nom)}) no-repeat center / contain; mask: url({_icone_masque(nom)}) no-repeat center / contain; }}' for cle, nom in ICONES_BOUTONS.items())}
.st-key-btn_accueil_dossier button {{ gap: 0.7rem; padding: 0.6rem 2rem !important; }}

/* Carte cliquable : un bouton invisible recouvre le contenu HTML */
[class*="st-key-clic_"] {{ position: relative; }}
[class*="st-key-clic_"] [data-testid="stElementContainer"]:has(.stButton) {{ position: absolute; inset: 0; z-index: 2; margin: 0; }}
[class*="st-key-clic_"] .stButton, [class*="st-key-clic_"] .stButton button {{ width: 100%; height: 100%; opacity: 0; cursor: pointer; }}

/* ---------- Champs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {{
    background: #fff !important; border-color: #D5DCE8 !important; border-radius: 8px !important;
}}
.st-key-f_recherche [data-baseweb="input"] {{ min-height: 3.1rem; padding-left: 2.6rem; border-radius: 10px !important; }}
.st-key-f_recherche {{ position: relative; }}
.st-key-f_recherche::before {{ content: ""; position: absolute; left: 0.95rem; top: 50%; transform: translateY(-50%); z-index: 1;
    width: 20px; height: 20px; background-color: {GRIS}; -webkit-mask: url({_icone_masque('recherche')}) no-repeat center / contain; mask: url({_icone_masque('recherche')}) no-repeat center / contain; }}
[data-baseweb="tag"] {{ background: #E5ECFB !important; color: {BLEU} !important; border-radius: 999px !important; font-weight: 700; }}
[data-baseweb="tag"] span {{ color: {BLEU} !important; }}
[data-testid="stExpander"] details {{ border-color: #DCE3EF; border-radius: 10px; background: #fff; }}
.stCheckbox label p {{ font-size: 0.95rem; color: #1F2A44; }}
.st-key-f_exp_min [data-testid="stSliderThumbValue"], .st-key-f_exp_min [data-testid="stSliderTickBarMin"],
.st-key-f_exp_min [data-testid="stSliderTickBarMax"] {{ display: none; }}

/* ---------- Journal d'analyse ---------- */
.cv-journal {{ display: flex; flex-direction: column-reverse; max-height: 300px; min-height: 300px; overflow-y: auto; padding: 0.4rem 1.4rem; }}
.cv-ligne {{ display: flex; align-items: center; gap: 2rem; padding: 0.95rem 0; border-bottom: 1px solid #E8EDF5; font-size: 0.95rem; }}
.cv-ligne:first-child {{ border-bottom: none; }}
.cv-heure {{ color: {GRIS}; width: 3rem; flex-shrink: 0; }}
.cv-ligne .cv-msg {{ flex: 1; color: #1F2A44; }}
.cv-spinner {{ width: 20px; height: 20px; border: 2.5px solid #D5DCE8; border-top-color: {BLEU}; border-radius: 50%; animation: cv-tourne 0.8s linear infinite; }}
@keyframes cv-tourne {{ to {{ transform: rotate(360deg); }} }}
.cv-progression {{ height: 12px; background: #E4EAF6; border-radius: 999px; overflow: hidden; margin-top: 0.9rem; }}
.cv-progression > div {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, {ROUGE} 0%, {ROUGE} 80%, {BLEU} 100%); transition: width 0.3s; }}

/* ---------- Tableaux ---------- */
.cv-table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: #fff; border: 1px solid #DCE3EF; border-radius: 14px; overflow: hidden; }}
.cv-table th {{ background: #EEF2FA; color: {BLEU}; font-weight: 700; font-size: 0.88rem; text-align: left; padding: 0.85rem 1.1rem; }}
.cv-table td {{ padding: 0.8rem 1.1rem; border-top: 1px solid #E8EDF5; font-size: 0.93rem; color: #1F2A44; vertical-align: middle; }}
.cv-table .cv-nom {{ font-weight: 700; color: #0F1B3D; }}
.cv-table .cv-fichier {{ color: {GRIS}; font-size: 0.82rem; }}
.cv-table .cv-droite {{ text-align: right; font-weight: 700; color: {BLEU}; }}

/* ---------- Accueil ---------- */
.cv-coin {{ position: fixed; top: 0; right: 0; width: 80px; height: 80px; background: {ROUGE}; clip-path: polygon(0 0, 100% 0, 100% 100%); z-index: 1; }}
.cv-hero {{ text-align: center; padding-top: 1rem; }}
.cv-hero-logo {{ display: inline-flex; align-items: center; gap: 1.1rem; }}
.cv-hero-nom {{ font-size: 3.6rem; font-weight: 900; letter-spacing: -0.02em; line-height: 1; }}
.cv-hero-accroche {{ color: {BLEU}; font-weight: 700; font-size: 1.1rem; margin-top: 1.4rem; }}
.cv-hero-texte {{ color: #3A4357; font-size: 1rem; margin: 1rem auto 0 auto; max-width: 360px; line-height: 1.55; }}
.cv-atouts {{ display: grid; grid-template-columns: repeat(3, 1fr); background: #fff; border: 1px solid #DCE3EF; border-radius: 14px; }}
.cv-atouts > div {{ text-align: center; padding: 1.2rem 0.4rem; }}
.cv-atouts .cv-muted {{ font-size: 0.85rem; }}
.cv-atouts > div + div {{ border-left: 1px solid #DCE3EF; }}
.cv-atout-titre {{ font-weight: 700; margin-top: 0.4rem; color: {BLEU}; }}
.cv-outil {{ background: #fff; border: 1px solid #DCE3EF; border-radius: 12px; padding: 0.85rem 0.9rem; min-height: 8.3rem; }}
.cv-outil-titre {{ font-weight: 700; color: #0F1B3D; font-size: 0.93rem; }}
.cv-outil-texte {{ color: {GRIS}; font-size: 0.82rem; margin-top: 0.3rem; line-height: 1.4; }}
[class*="st-key-clic_outil"]:hover .cv-outil {{ border-color: {BLEU}; }}

/* ---------- Validation ---------- */
.cv-file {{ border: 1px solid #DCE3EF; border-radius: 10px; padding: 0.75rem 0.9rem; background: #fff; }}
.cv-file-nom {{ font-weight: 700; color: #0F1B3D; font-size: 0.95rem; }}
.cv-file-info {{ color: {GRIS}; font-size: 0.85rem; margin-top: 0.15rem; }}
.cv-file.actif {{ background: #FCE4E6; border: 1.5px solid {ROUGE}; }}
.cv-file.actif .cv-file-info {{ color: #B3121F; font-weight: 600; }}
[class*="st-key-clic_file"]:hover .cv-file:not(.actif) {{ border-color: {BLEU}; }}
.cv-suggestion {{ display: flex; align-items: center; gap: 0.9rem; border: 1px solid #DCE3EF; border-radius: 10px; padding: 0.75rem 1rem; background: #fff; }}
.cv-suggestion.actif {{ background: #F1F4FB; border: 1.5px solid {BLEU}; }}
.cv-radio {{ width: 18px; height: 18px; border-radius: 50%; border: 2px solid #9AA3B5; flex-shrink: 0; }}
.cv-suggestion.actif .cv-radio {{ border: 5px solid {ROUGE}; }}
.cv-suggestion-nom {{ font-weight: 600; width: 38%; color: #0F1B3D; }}
.cv-suggestion .cv-barre {{ flex: 1; height: 9px; }}
.cv-suggestion-pct {{ width: 3.6rem; text-align: right; font-weight: 700; color: {BLEU}; }}
.cv-compteurs {{ display: flex; gap: 0.7rem; justify-content: flex-end; }}
.cv-compteur {{ padding: 0.55rem 1rem; border-radius: 10px; font-weight: 600; font-size: 0.92rem; display: flex; gap: 0.6rem; align-items: center; }}
.cv-compteur b {{ font-size: 1.15rem; }}

/* ---------- Apprentissage ---------- */
.cv-precision {{ display: grid; grid-template-columns: 11rem 1fr 3.5rem; align-items: center; gap: 1rem; padding: 0.45rem 0; font-size: 0.95rem; }}
.cv-precision .pct {{ text-align: right; font-weight: 700; }}
.cv-correction {{ padding: 0.75rem 0; border-bottom: 1px solid #E8EDF5; }}
.cv-correction s {{ color: {GRIS}; }}
"""


def injecter_css():
    afficher(f"<style>{CSS}</style>")
