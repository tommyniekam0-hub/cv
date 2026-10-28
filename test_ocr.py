import sys
import time
import os

import fitz
from rapidocr_onnxruntime import RapidOCR

# ============================================================
# CONFIGURATION
# ============================================================

# Dossier contenant vos CV : python test_ocr.py [dossier] (défaut : cv_a_traiter)
DOSSIER_CV = sys.argv[1] if len(sys.argv) > 1 else "cv_a_traiter"


def texte_resultat(resultat):
    """Normalise la sortie de RapidOCR (compatible tuple v1.2/v1.3 et objet v1.4+)."""
    if resultat is None:
        return ""
    if isinstance(resultat, tuple):
        resultat = resultat[0]
    if resultat is None:
        return ""
    if hasattr(resultat, 'txts'):
        return "\n".join(t for t in resultat.txts if t)
    return "\n".join(item[1] for item in resultat if len(item) > 1 and item[1])


# ============================================================
# CHARGEMENT DU MODÈLE
# ============================================================
print("=" * 70)
print("CHARGEMENT DU MODÈLE RAPIDOCR...")
print("=" * 70)

debut = time.time()
reader = RapidOCR()
print(f"✅ Modèle chargé en {time.time() - debut:.1f} secondes\n")

# ============================================================
# RECHERCHE AUTOMATIQUE DU 1er CV
# ============================================================
if not os.path.isdir(DOSSIER_CV):
    print(f"❌ Dossier introuvable : {DOSSIER_CV}")
    print("💡 Usage : python test_ocr.py <dossier_des_cv>")
    sys.exit(1)

fichiers = [f for f in os.listdir(DOSSIER_CV)
            if f.lower().endswith(('.pdf', '.docx', '.png', '.jpg', '.jpeg'))]

if not fichiers:
    print(f"❌ Aucun CV trouvé dans {DOSSIER_CV}")
    print("💡 Formats acceptés : PDF, DOCX, PNG, JPG")
    sys.exit(1)

print(f"📁 Dossier : {DOSSIER_CV}")
print(f"📄 {len(fichiers)} fichier(s) trouvé(s) :")
for f in fichiers:
    print(f"   - {f}")

chemin_cv = os.path.join(DOSSIER_CV, fichiers[0])

# ============================================================
# ANALYSE
# ============================================================
print("\n" + "=" * 70)
print(f"ANALYSE : {fichiers[0]}")
print("=" * 70)

texte_complet = []
try:
    doc = fitz.open(chemin_cv)
    print(f"\n✅ Fichier ouvert - {len(doc)} page(s)\n")

    for i, page in enumerate(doc):
        print(f"{'='*70}")
        print(f"=== PAGE {i+1} - TEXTE OCR ===")
        print(f"{'='*70}\n")

        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")

        debut = time.time()
        resultat = reader(img_bytes)
        duree = time.time() - debut

        texte = texte_resultat(resultat)
        texte_complet.append(texte)
        print(texte)
        print(f"\n⏱️ Temps : {duree:.1f}s\n")

    doc.close()
    print("=" * 70)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERREUR : {e}")

with open("resultat_ocr.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(texte_complet))

print("\n✅ Résultat sauvegardé dans : resultat_ocr.txt")
