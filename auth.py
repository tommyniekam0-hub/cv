# ============================================================
# auth.py
# Comptes utilisateurs : connexion, rôles (admin / user) et permissions.
# Les mots de passe sont hachés (PBKDF2-SHA256, sel aléatoire) dans
# utilisateurs.json. Ce module n'utilise pas Streamlit : il peut être
# testé ou utilisé en ligne de commande (voir tout en bas).
# ============================================================

import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
import time
from datetime import datetime

FICHIER_UTILISATEURS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utilisateurs.json")

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLES = {ROLE_ADMIN: "Administrateur", ROLE_USER: "Utilisateur"}

# Ce qu'un administrateur peut accorder à un utilisateur.
# Un administrateur a toujours toutes les permissions.
PERMISSIONS = {
    'analyser': "Analyser les CV d'un dossier",
    'dossier': "Choisir un autre dossier à analyser (accès aux fichiers du serveur)",
    'emails': "Récupérer et analyser les CV de la boîte mail",
    'resultats': "Voir les résultats",
    'filtrer': "Filtrer les CV",
    'validation': "Valider et corriger les classements",
    'apprentissage': "Gérer l'apprentissage du modèle",
    'correspondance': "Comparer les CV à une offre",
    'exporter': "Exporter (Excel, copie des CV filtrés)",
}
PERMISSIONS_PAR_DEFAUT = ['analyser', 'resultats', 'filtrer', 'validation', 'correspondance']

MDP_LONGUEUR_MIN = 8
TENTATIVES_MAX = 5           # échecs de connexion avant blocage
DUREE_BLOCAGE = 5 * 60       # secondes
_ITERATIONS = 600_000
_IDENTIFIANT = re.compile(r'^[a-z0-9._-]{3,32}$')

_verrou = threading.RLock()  # plusieurs sessions Streamlit partagent ce processus
_echecs = {}                 # identifiant → (nombre d'échecs, heure du dernier échec)


# ------------------------------------------------------------
# Mots de passe
# ------------------------------------------------------------
def hacher_mot_de_passe(mdp, sel=None, iterations=_ITERATIONS):
    sel = sel or secrets.token_bytes(16)
    empreinte = hashlib.pbkdf2_hmac('sha256', mdp.encode('utf-8'), sel, iterations)
    return f"pbkdf2_sha256${iterations}${sel.hex()}${empreinte.hex()}"


def verifier_mot_de_passe(mdp, stocke):
    try:
        algo, iterations, sel, empreinte = stocke.split('$')
        if algo != 'pbkdf2_sha256':
            return False
        calcule = hashlib.pbkdf2_hmac('sha256', mdp.encode('utf-8'), bytes.fromhex(sel), int(iterations))
        return hmac.compare_digest(calcule.hex(), empreinte)
    except (ValueError, AttributeError):
        return False


# Haché factice : un identifiant inconnu prend autant de temps qu'un mauvais mot de passe
# (on ne peut pas deviner quels comptes existent en mesurant le temps de réponse)
_HACHE_FACTICE = hacher_mot_de_passe(secrets.token_urlsafe(16))


def generer_mot_de_passe():
    """Mot de passe temporaire lisible (sans caractères ambigus)"""
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(alphabet) for _ in range(12))


def erreur_mot_de_passe(mdp, identifiant=""):
    """Message d'erreur si le mot de passe est trop faible, sinon None"""
    if len(mdp) < MDP_LONGUEUR_MIN:
        return f"Le mot de passe doit contenir au moins {MDP_LONGUEUR_MIN} caractères."
    if identifiant and mdp.lower() == identifiant.lower():
        return "Le mot de passe doit être différent de l'identifiant."
    if mdp.isdigit() or mdp.isalpha():
        return "Le mot de passe doit mélanger lettres et chiffres (ou symboles)."
    return None


def normaliser_identifiant(identifiant):
    return (identifiant or "").strip().lower()


# ------------------------------------------------------------
# Fichier des utilisateurs
# ------------------------------------------------------------
def charger_utilisateurs():
    with _verrou:
        if not os.path.exists(FICHIER_UTILISATEURS):
            return {}
        with open(FICHIER_UTILISATEURS, 'r', encoding='utf-8') as f:
            return json.load(f)


def _sauvegarder(utilisateurs):
    """Écriture atomique : un fichier à moitié écrit ne peut pas bloquer toutes les connexions"""
    with _verrou:
        dossier = os.path.dirname(FICHIER_UTILISATEURS)
        fd, temporaire = tempfile.mkstemp(dir=dossier, prefix=".utilisateurs_", suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(utilisateurs, f, indent=2, ensure_ascii=False)
            os.replace(temporaire, FICHIER_UTILISATEURS)
        except BaseException:
            if os.path.exists(temporaire):
                os.remove(temporaire)
            raise


def aucun_utilisateur():
    return not charger_utilisateurs()


def obtenir(identifiant):
    return charger_utilisateurs().get(normaliser_identifiant(identifiant))


def _nb_admins_actifs(utilisateurs, sauf=None):
    return sum(1 for ident, u in utilisateurs.items()
               if ident != sauf and u['role'] == ROLE_ADMIN and u.get('actif', True))


# ------------------------------------------------------------
# Connexion
# ------------------------------------------------------------
def secondes_blocage(identifiant):
    """Secondes restantes avant de pouvoir réessayer (0 si le compte n'est pas bloqué)"""
    with _verrou:
        nb, dernier = _echecs.get(normaliser_identifiant(identifiant), (0, 0))
    if nb < TENTATIVES_MAX:
        return 0
    return max(0, int(dernier + DUREE_BLOCAGE - time.time()))


def authentifier(identifiant, mdp):
    """(utilisateur, None) si la connexion réussit, sinon (None, message d'erreur)"""
    ident = normaliser_identifiant(identifiant)
    attente = secondes_blocage(ident)
    if attente:
        return None, f"Trop de tentatives. Réessayez dans {attente // 60 + 1} minute(s)."

    utilisateur = charger_utilisateurs().get(ident)
    ok = verifier_mot_de_passe(mdp, utilisateur['hash'] if utilisateur else _HACHE_FACTICE)
    if not utilisateur or not ok:
        with _verrou:
            nb, _ = _echecs.get(ident, (0, 0))
            _echecs[ident] = (nb + 1, time.time())
        return None, "Identifiant ou mot de passe incorrect."
    if not utilisateur.get('actif', True):
        return None, "Ce compte est désactivé. Contactez un administrateur."

    with _verrou:
        _echecs.pop(ident, None)
        utilisateurs = charger_utilisateurs()
        utilisateurs[ident]['derniere_connexion'] = datetime.now().isoformat(timespec='seconds')
        _sauvegarder(utilisateurs)
    return utilisateurs[ident], None


def a_permission(utilisateur, permission):
    if not utilisateur:
        return False
    if utilisateur['role'] == ROLE_ADMIN:
        return True
    return permission in utilisateur.get('permissions', [])


# ------------------------------------------------------------
# Gestion des comptes (réservée aux administrateurs côté interface)
# ------------------------------------------------------------
def creer_utilisateur(identifiant, nom, mdp, role=ROLE_USER, permissions=None, doit_changer_mdp=True):
    """(True, message) ou (False, erreur)"""
    ident = normaliser_identifiant(identifiant)
    if not _IDENTIFIANT.match(ident):
        return False, "Identifiant invalide : 3 à 32 caractères (lettres, chiffres, point, tiret, tiret bas)."
    if role not in ROLES:
        return False, "Rôle inconnu."
    erreur = erreur_mot_de_passe(mdp, ident)
    if erreur:
        return False, erreur
    with _verrou:
        utilisateurs = charger_utilisateurs()
        if ident in utilisateurs:
            return False, f"L'identifiant « {ident} » existe déjà."
        utilisateurs[ident] = {
            'identifiant': ident,
            'nom': (nom or "").strip() or ident,
            'role': role,
            'hash': hacher_mot_de_passe(mdp),
            'permissions': [p for p in (permissions if permissions is not None else PERMISSIONS_PAR_DEFAUT)
                            if p in PERMISSIONS],
            'actif': True,
            'doit_changer_mdp': doit_changer_mdp,
            'cree_le': datetime.now().isoformat(timespec='seconds'),
            'derniere_connexion': None,
        }
        _sauvegarder(utilisateurs)
    return True, f"Compte « {ident} » créé."


def modifier_utilisateur(identifiant, nom=None, role=None, permissions=None, actif=None):
    ident = normaliser_identifiant(identifiant)
    with _verrou:
        utilisateurs = charger_utilisateurs()
        u = utilisateurs.get(ident)
        if not u:
            return False, "Compte introuvable."
        perd_admin = (u['role'] == ROLE_ADMIN and u.get('actif', True)
                      and ((role is not None and role != ROLE_ADMIN) or actif is False))
        if perd_admin and _nb_admins_actifs(utilisateurs, sauf=ident) == 0:
            return False, "Impossible : il doit rester au moins un administrateur actif."
        if nom is not None:
            u['nom'] = nom.strip() or ident
        if role is not None:
            if role not in ROLES:
                return False, "Rôle inconnu."
            u['role'] = role
        if permissions is not None:
            u['permissions'] = [p for p in permissions if p in PERMISSIONS]
        if actif is not None:
            u['actif'] = bool(actif)
        _sauvegarder(utilisateurs)
    return True, f"Compte « {ident} » mis à jour."


def definir_mot_de_passe(identifiant, mdp, doit_changer_mdp=False):
    ident = normaliser_identifiant(identifiant)
    erreur = erreur_mot_de_passe(mdp, ident)
    if erreur:
        return False, erreur
    with _verrou:
        utilisateurs = charger_utilisateurs()
        if ident not in utilisateurs:
            return False, "Compte introuvable."
        utilisateurs[ident]['hash'] = hacher_mot_de_passe(mdp)
        utilisateurs[ident]['doit_changer_mdp'] = doit_changer_mdp
        _sauvegarder(utilisateurs)
        _echecs.pop(ident, None)
    return True, "Mot de passe modifié."


def changer_son_mot_de_passe(identifiant, ancien, nouveau):
    """Changement par l'utilisateur lui-même : l'ancien mot de passe est exigé"""
    u = obtenir(identifiant)
    if not u or not verifier_mot_de_passe(ancien, u['hash']):
        return False, "Mot de passe actuel incorrect."
    if ancien == nouveau:
        return False, "Le nouveau mot de passe doit être différent de l'ancien."
    return definir_mot_de_passe(identifiant, nouveau, doit_changer_mdp=False)


def supprimer_utilisateur(identifiant):
    ident = normaliser_identifiant(identifiant)
    with _verrou:
        utilisateurs = charger_utilisateurs()
        u = utilisateurs.get(ident)
        if not u:
            return False, "Compte introuvable."
        if u['role'] == ROLE_ADMIN and _nb_admins_actifs(utilisateurs, sauf=ident) == 0:
            return False, "Impossible : il doit rester au moins un administrateur actif."
        del utilisateurs[ident]
        _sauvegarder(utilisateurs)
    return True, f"Compte « {ident} » supprimé."


# ------------------------------------------------------------
# Ligne de commande : créer un admin ou réinitialiser son mot de passe
#   python auth.py admin <identifiant>
# (utile si plus personne ne peut se connecter)
# ------------------------------------------------------------
if __name__ == "__main__":
    import getpass
    import sys

    if len(sys.argv) != 3 or sys.argv[1] != "admin":
        print("Usage : python auth.py admin <identifiant>")
        sys.exit(1)
    ident = normaliser_identifiant(sys.argv[2])
    mdp = getpass.getpass("Nouveau mot de passe : ")
    if mdp != getpass.getpass("Confirmez le mot de passe : "):
        print("Les mots de passe ne correspondent pas.")
        sys.exit(1)
    if obtenir(ident):
        ok, msg = definir_mot_de_passe(ident, mdp)
        if ok:
            ok, msg = modifier_utilisateur(ident, role=ROLE_ADMIN, actif=True)
    else:
        ok, msg = creer_utilisateur(ident, ident, mdp, role=ROLE_ADMIN, doit_changer_mdp=False)
    print(msg)
    sys.exit(0 if ok else 1)
