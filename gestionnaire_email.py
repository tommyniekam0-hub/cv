# ============================================================
# gestionnaire_email.py
# Module de connexion IMAP pour recevoir les CV par email
# ============================================================

import os
import re
import base64
import imaplib
import email
from email.header import decode_header
from pathlib import Path
import quopri
from datetime import timedelta
from urllib.parse import unquote

# Mois en anglais pour les critères IMAP (indépendant de la langue du système)
_MOIS_IMAP = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def date_imap(d):
    """Formate une date au format IMAP (ex : 09-Nov-2026)"""
    return f"{d.day:02d}-{_MOIS_IMAP[d.month - 1]}-{d.year}"


EXTENSIONS_CV = ('.pdf', '.docx', '.doc')
# Nombre d'emails dont on lit la structure en une seule requête
TAILLE_LOT = 50
# Délai max d'attente du serveur (évite une vérification bloquée indéfiniment)
DELAI_SERVEUR = 60


def _texte(v):
    if v is None:
        return ''
    return v.decode('utf-8', errors='replace') if isinstance(v, bytes) else str(v)


def _analyser_imap(buf):
    """Découpe une réponse IMAP brute en valeurs : listes (...), chaînes "..." ou {n}, atomes, None (NIL)"""
    pos, n = 0, len(buf)

    def blancs():
        nonlocal pos
        while pos < n and buf[pos] in b' \r\n\t':
            pos += 1

    def valeur():
        nonlocal pos
        blancs()
        c = buf[pos:pos + 1]
        if c == b'(':
            pos += 1
            liste = []
            while True:
                blancs()
                if pos >= n:
                    return liste
                if buf[pos:pos + 1] == b')':
                    pos += 1
                    return liste
                liste.append(valeur())
        if c == b'"':
            pos += 1
            out = bytearray()
            while pos < n and buf[pos:pos + 1] != b'"':
                if buf[pos:pos + 1] == b'\\':
                    pos += 1
                out += buf[pos:pos + 1]
                pos += 1
            pos += 1
            return bytes(out)
        if c == b'{':
            fin = buf.index(b'}', pos)
            taille = int(buf[pos + 1:fin])
            pos = fin + 1
            v = buf[pos:pos + taille]
            pos += taille
            return v
        # Atome ; "BODY[HEADER.FIELDS (FROM SUBJECT)]" garde ses crochets et espaces
        debut, prof = pos, 0
        while pos < n:
            ch = buf[pos:pos + 1]
            if ch == b'[':
                prof += 1
            elif ch == b']':
                prof -= 1
            elif prof == 0 and ch in (b' ', b'(', b')', b'\r', b'\n'):
                break
            pos += 1
        if pos == debut:  # ")" en trop
            pos += 1
            return None
        atome = buf[debut:pos]
        return None if atome.upper() == b'NIL' else atome

    valeurs = []
    while True:
        blancs()
        if pos >= n:
            return valeurs
        valeurs.append(valeur())


def _decouper_reponses_fetch(data):
    """Listes [CLE, valeur, CLE, valeur...] de chaque email d'une réponse FETCH.
    imaplib sépare les littéraux {n} en tuples : on recompose le flux brut."""
    flux = bytearray()
    for d in data or []:
        if isinstance(d, tuple):
            flux += d[0] + d[1]
        elif isinstance(d, bytes):
            flux += d + b' '
    reponses = []
    for v in _analyser_imap(bytes(flux)):
        if isinstance(v, list):
            reponses.append([k.upper() if isinstance(k, bytes) and i % 2 == 0 else k for i, k in enumerate(v)])
    return reponses


def _param(params, cle):
    """Valeur d'un paramètre MIME (name, filename), y compris l'encodage RFC 2231 (filename*=utf-8''...)"""
    if not isinstance(params, list):
        return None
    d = {_texte(k).lower(): _texte(v) for k, v in zip(params[::2], params[1::2])}
    if d.get(cle):
        return d[cle]
    morceaux = sorted((k for k in d if k.startswith(cle + '*')), key=lambda k: int(re.sub(r'\D', '', k) or 0))
    if not morceaux:
        return None
    valeur = ''.join(d[k] for k in morceaux)
    if morceaux[0].endswith('*') and valeur.count("'") >= 2:
        charset, _, reste = valeur.split("'", 2)
        try:
            return unquote(reste, encoding=charset or 'utf-8', errors='replace')
        except LookupError:
            return unquote(reste)
    return valeur


def _parties_jointes(s, numero=''):
    """(n° de partie IMAP, nom de fichier, encodage, taille) de chaque fichier joint d'un BODYSTRUCTURE"""
    if not isinstance(s, list) or not s:
        return
    if isinstance(s[0], list):  # multipart : sous-parties puis sous-type
        i = 0
        for enfant in s:
            if not isinstance(enfant, list):
                break
            i += 1
            yield from _parties_jointes(enfant, f"{numero}.{i}" if numero else str(i))
        return
    num = numero or '1'
    type_, sous_type = _texte(s[0]).lower(), _texte(s[1] if len(s) > 1 else b'').lower()
    # Email transféré en pièce jointe : on regarde ses propres pièces jointes
    if type_ == 'message' and sous_type == 'rfc822' and len(s) > 8 and isinstance(s[8], list):
        interne = s[8]
        yield from _parties_jointes(interne, num if interne and isinstance(interne[0], list) else num + '.1')
        return
    nom = None
    for extension in s[7:]:
        # Disposition : ("attachment" ("filename" "cv.pdf"))
        if isinstance(extension, list) and len(extension) >= 2 and isinstance(extension[1], list):
            nom = _param(extension[1], 'filename')
            if nom:
                break
    nom = nom or _param(s[2] if len(s) > 2 else None, 'name')
    if nom:
        try:
            taille = int(s[6])
        except (TypeError, ValueError, IndexError):
            taille = 0
        yield num, nom, _texte(s[5] if len(s) > 5 else b'').lower(), taille


def _decoder_contenu(brut, encodage):
    if encodage == 'base64':
        return base64.b64decode(brut)
    if encodage == 'quoted-printable':
        return quopri.decodestring(brut)
    return brut

# Dossier local où on télécharge les CV
DOSSIER_CV_EMAIL = "cv_recus_email"
os.makedirs(DOSSIER_CV_EMAIL, exist_ok=True)


def encoder_nom_dossier_imap(nom):
    """Encode un nom de dossier en UTF-7 modifié (RFC 3501) et le met entre guillemets.
    Nécessaire pour les noms avec accents ou espaces (ex: "CV traités")."""
    resultat, tampon = [], []

    def vider_tampon():
        if tampon:
            b64 = base64.b64encode(''.join(tampon).encode('utf-16-be')).decode('ascii')
            resultat.append('&' + b64.rstrip('=').replace('/', ',') + '-')
            tampon.clear()

    for c in nom:
        if 0x20 <= ord(c) <= 0x7e:
            vider_tampon()
            resultat.append('&-' if c == '&' else c)
        else:
            tampon.append(c)
    vider_tampon()
    encode = ''.join(resultat).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{encode}"'


class GestionnaireEmail:
    """Gère la connexion IMAP et la récupération des CV par email"""
    
    def __init__(self, serveur, port, email_address, mot_de_passe, dossier_traites="CV traités"):
        self.serveur = serveur
        self.port = int(port)
        self.email_address = email_address
        self.mot_de_passe = mot_de_passe
        self.dossier_traites = dossier_traites
        self.connexion = None
        self.dossier_local = DOSSIER_CV_EMAIL
        os.makedirs(self.dossier_local, exist_ok=True)
    
    def se_connecter(self):
        """Établit la connexion IMAP"""
        try:
            self.connexion = imaplib.IMAP4_SSL(self.serveur, self.port, timeout=DELAI_SERVEUR)
            self.connexion.login(self.email_address, self.mot_de_passe)
            return True, "Connexion réussie"
        except imaplib.IMAP4.error as e:
            return False, f"Erreur d'authentification : {str(e)}"
        except Exception as e:
            return False, f"Erreur de connexion : {str(e)}"
    
    def se_deconnecter(self):
        """Ferme la connexion proprement"""
        try:
            if self.connexion:
                try:
                    self.connexion.close()
                except:
                    pass
                self.connexion.logout()
                self.connexion = None
        except:
            pass
    
    def _decoder_sujet(self, sujet):
        """Décode le sujet (parfois encodé)"""
        if not sujet:
            return "(Sans sujet)"
        try:
            parties = decode_header(sujet)
            resultat = ""
            for contenu, encodage in parties:
                if isinstance(contenu, bytes):
                    resultat += contenu.decode(encodage or 'utf-8', errors='ignore')
                else:
                    resultat += contenu
            return resultat
        except:
            return str(sujet)
    
    def _decoder_expediteur(self, expediteur):
        """Décode l'expéditeur"""
        try:
            parties = decode_header(expediteur)
            resultat = ""
            for contenu, encodage in parties:
                if isinstance(contenu, bytes):
                    resultat += contenu.decode(encodage or 'utf-8', errors='ignore')
                else:
                    resultat += contenu
            return resultat
        except:
            return str(expediteur)
    
    def _extraire_email_expediteur(self, expediteur):
        """Extrait juste l'adresse email de l'expéditeur"""
        m = re.search(r'[\w\.-]+@[\w\.-]+', expediteur)
        return m.group(0) if m else expediteur
    
    def _nettoyer_nom_fichier(self, nom):
        """Nettoie le nom du fichier pour éviter les caractères interdits"""
        # Enlever les retours à la ligne et tabulations
        nom = nom.replace('\r', '').replace('\n', '').replace('\t', '')
        # Enlever les espaces multiples
        nom = re.sub(r'\s+', ' ', nom)
        # Enlever les caractères interdits
        nom = re.sub(r'[<>:"/\\|?*]', '_', nom)
        # Enlever les espaces en début/fin
        nom = nom.strip()
        return nom[:200]
    
    def recuperer_emails(self, max_emails=50, date_debut=None, date_fin=None, progression=None):
        """Récupère les emails de la boîte de réception qui ont des CV en pièce jointe.

        date_debut / date_fin (datetime.date, incluses) limitent la période analysée.
        progression(fait, total) est appelée après chaque lot d'emails lus.
        Seuls l'en-tête et la structure sont lus : les CV sont téléchargés
        par telecharger_pieces_jointes() au moment de l'analyse.

        Tous les emails sont lus (pas seulement les non lus) : les emails traités sont
        déplacés hors de la boîte, donc ceux qui restent sont à traiter. Les messages
        ne sont pas marqués comme lus et une pièce jointe déjà téléchargée n'est pas
        téléchargée une seconde fois."""
        if not self.connexion:
            ok, msg = self.se_connecter()
            if not ok:
                return [], msg

        emails_trouves = []

        try:
            self.connexion.select("INBOX", readonly=True)
            # UID (stable) plutôt que numéro de séquence (change après chaque déplacement)
            criteres = ["UNDELETED"]
            if date_debut:
                criteres += ["SINCE", date_imap(date_debut)]
            if date_fin:
                # BEFORE est exclusif : on prend le lendemain pour inclure le dernier jour
                criteres += ["BEFORE", date_imap(date_fin + timedelta(days=1))]
            status, messages = self.connexion.uid("search", None, *criteres)
            
            if status != "OK":
                return [], "Impossible de lire la boîte"
            
            ids_emails = messages[0].split()
            ids_emails = ids_emails[-max_emails:] if max_emails and len(ids_emails) > max_emails else ids_emails
            total = len(ids_emails)

            # On ne télécharge que l'en-tête et la structure des emails (quelques Ko),
            # par lots : les pièces jointes sont téléchargées au moment de l'analyse.
            for debut in range(0, total, TAILLE_LOT):
                if progression:
                    progression(debut, total)
                lot = ids_emails[debut:debut + TAILLE_LOT]
                status, data = self.connexion.uid(
                    "fetch", b",".join(lot),
                    "(UID BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if status != "OK":
                    continue
                for reponse in _decouper_reponses_fetch(data):
                    try:
                        em = self._email_depuis_structure(reponse)
                    except Exception as e:
                        print(f"Erreur lecture email : {e}")
                        continue
                    if em:
                        emails_trouves.append(em)

            if progression:
                progression(total, total)
            # Les plus récents en premier
            emails_trouves.sort(key=lambda e: int(e['id']), reverse=True)
            return emails_trouves, f"{len(emails_trouves)} email(s) avec CV trouvé(s) sur {total} email(s) lu(s)"

        except Exception as e:
            return [], f"Erreur : {str(e)}"

    def _email_depuis_structure(self, reponse):
        """Email (dict) à partir d'une réponse FETCH, ou None s'il n'a pas de CV en pièce jointe"""
        champs = dict(zip(reponse[::2], reponse[1::2]))
        uid = _texte(champs.get(b'UID'))
        structure = champs.get(b'BODYSTRUCTURE')
        entete = next((v for k, v in champs.items() if isinstance(k, bytes) and k.startswith(b'BODY[')), b'')
        if not uid or not isinstance(structure, list):
            return None

        pieces_jointes = []
        for numero, nom, encodage, taille in _parties_jointes(structure):
            nom_decoded = self._nettoyer_nom_fichier(self._decoder_sujet(nom))
            if os.path.splitext(nom_decoded)[1].lower() not in EXTENSIONS_CV:
                continue
            # Nom stable (UID + n° de partie) : pas de doublon ni d'écrasement
            nom_sauvegarde = f"{uid}_{numero.replace('.', '-')}_{nom_decoded}"
            pieces_jointes.append({
                'nom_original': nom_decoded,
                'nom_sauvegarde': nom_sauvegarde,
                'chemin': os.path.join(self.dossier_local, nom_sauvegarde),
                'partie': numero,
                'encodage': encodage,
                # Taille encodée : le base64 grossit le fichier d'un tiers
                'taille': taille * 3 // 4 if encodage == 'base64' else taille,
            })
        if not pieces_jointes:
            return None

        message = email.message_from_bytes(entete if isinstance(entete, bytes) else b'')
        expediteur = self._decoder_expediteur(message.get("From", ""))
        return {
            'id': uid,
            'expediteur': expediteur,
            'email_expediteur': self._extraire_email_expediteur(expediteur),
            'sujet': self._decoder_sujet(message.get("Subject", "")),
            'date': message.get("Date", ""),
            'pieces_jointes': pieces_jointes,
            'nb_cv': len(pieces_jointes)
        }

    def telecharger_pieces_jointes(self, em):
        """Télécharge les CV d'un email (seulement les pièces jointes, pas le reste du message).
        Une pièce jointe déjà présente sur le disque n'est pas retéléchargée."""
        if not self.connexion:
            ok, msg = self.se_connecter()
            if not ok:
                return False, msg
        self.connexion.select("INBOX", readonly=True)
        for pj in em['pieces_jointes']:
            if os.path.exists(pj['chemin']):
                continue
            partie = pj.get('partie')
            if not partie:
                continue
            status, data = self.connexion.uid("fetch", em['id'], f"(BODY.PEEK[{partie}])")
            brut = next((d[1] for d in data or [] if isinstance(d, tuple)), None)
            if status != "OK" or brut is None:
                return False, f"Téléchargement impossible : {pj['nom_original']}"
            contenu = _decoder_contenu(brut, pj.get('encodage', ''))
            with open(pj['chemin'], 'wb') as f:
                f.write(contenu)
            pj['taille'] = len(contenu)
        return True, "OK"
    
    def deplacer_email(self, email_id, dossier_destination=None):
        """Déplace un email traité vers un dossier"""
        if not dossier_destination:
            dossier_destination = self.dossier_traites
        
        try:
            if not self.connexion:
                ok, msg = self.se_connecter()
                if not ok:
                    return False, msg
            # COPY/STORE exigent une boîte sélectionnée
            self.connexion.select("INBOX")
            dossier_imap = encoder_nom_dossier_imap(dossier_destination)
            try:
                self.connexion.create(dossier_imap)
            except:
                pass
            
            capacites = getattr(self.connexion, 'capabilities', ())
            # MOVE (RFC 6851) : déplacement atomique de ce seul email
            if 'MOVE' in capacites:
                status, _ = self.connexion.uid("move", email_id, dossier_imap)
                if status == "OK":
                    return True, f"Email déplacé dans '{dossier_destination}'"

            status, _ = self.connexion.uid("copy", email_id, dossier_imap)
            if status != "OK":
                return False, f"Copie impossible vers '{dossier_destination}'"
            self.connexion.uid("store", email_id, '+FLAGS', '(\\Deleted)')
            if 'UIDPLUS' in capacites:
                # Supprime uniquement cet email (un EXPUNGE simple effacerait aussi
                # les autres emails déjà marqués comme supprimés dans la boîte)
                self.connexion.uid("expunge", email_id)
                return True, f"Email déplacé dans '{dossier_destination}'"
            # Serveur trop ancien : l'email est copié et marqué supprimé, sans purge globale
            return True, (f"Email copié dans '{dossier_destination}' et marqué comme supprimé "
                          f"dans la boîte de réception")
        except Exception as e:
            return False, f"Erreur : {str(e)}"


def tester_connexion(serveur, port, email_address, mot_de_passe):
    """Teste la connexion IMAP avec les paramètres fournis"""
    try:
        gestionnaire = GestionnaireEmail(serveur, port, email_address, mot_de_passe)
        ok, msg = gestionnaire.se_connecter()
        gestionnaire.se_deconnecter()
        return ok, msg
    except Exception as e:
        return False, f"Erreur : {str(e)}"