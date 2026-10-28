import sys
import fitz
import re

# Usage : python debug_cv.py chemin/vers/le_cv_qui_bug.pdf
if len(sys.argv) != 2:
    print("Usage : python debug_cv.py <chemin_du_cv.pdf>")
    sys.exit(1)
chemin = sys.argv[1]

doc = fitz.open(chemin)
texte = ""
for page in doc:
    texte += page.get_text() + "\n"
doc.close()

print("=" * 70)
print("TEXTE EXTRAIT (200 premiers caractères) :")
print("=" * 70)
print(repr(texte[:200]))
print()

print("=" * 70)
print("PREMIÈRES 5 LIGNES NON VIDES :")
print("=" * 70)
lignes = [l.strip() for l in texte.split('\n') if l.strip()]
for i, ligne in enumerate(lignes[:5]):
    print(f"Ligne {i+1}: {repr(ligne)}")

print()
print("=" * 70)
print("MOTS EN MAJUSCULES (candidats noms) :")
print("=" * 70)
mots = re.findall(r'\b[A-ZÀ-Ý]{3,20}\b', texte[:800])
print(mots[:20])

print()
print("=" * 70)
print("TEST DE LA RÈGLE 'LIGNE 1-3' :")
print("=" * 70)

MOTS_INTERDITS = {
    'COMMUNICATION', 'INNOVATION', 'PRODUIT', 'INTÉRÊT',
    'ANNÉE', 'TCF', 'MARKETING', 'DIGITAL', 'FORMATION',
    'EXPÉRIENCES', 'COMPÉTENCES', 'LANGUES', 'CERTIFICATIONS'
}

for ligne in lignes[:3]:
    ligne_clean = re.sub(r'[·•\-/–—|]', ' ', ligne)
    ligne_clean = re.sub(r'\s+', ' ', ligne_clean).strip()
    
    print(f"\nLigne analysée: {repr(ligne_clean)}")
    print(f"  Longueur: {len(ligne_clean)}")
    
    if len(ligne_clean) < 4 or len(ligne_clean) > 45:
        print(f"  ❌ Rejetée : longueur invalide")
        continue
    
    mots_ligne = re.findall(r'\b[A-Za-zÀ-ÿ]{2,20}\b', ligne_clean)
    print(f"  Mots trouvés: {mots_ligne}")
    
    if not (2 <= len(mots_ligne) <= 3):
        print(f"  ❌ Rejetée : pas 2-3 mots")
        continue
    
    if any(m.upper() in MOTS_INTERDITS for m in mots_ligne):
        print(f"  ❌ Rejetée : mot interdit trouvé")
        continue
    
    if not all(m[0].isupper() for m in mots_ligne):
        print(f"  ❌ Rejetée : pas tous en majuscule")
        continue
    
    print(f"  ✅ ACCEPTÉE : {mots_ligne[0]} {mots_ligne[1]}")
    break