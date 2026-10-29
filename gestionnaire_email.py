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
            self.connexion = imaplib.IMAP4_SSL(self.serveur, self.port)
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
    
    def recuperer_emails(self, max_emails=50):
        """Récupère les emails de la boîte de réception qui ont des CV en pièce jointe.

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
            self.connexion.select("INBOX")
            # UID (stable) plutôt que numéro de séquence (change après chaque déplacement)
            status, messages = self.connexion.uid("search", None, "UNDELETED")
            
            if status != "OK":
                return [], "Impossible de lire la boîte"
            
            ids_emails = messages[0].split()
            ids_emails = ids_emails[-max_emails:] if len(ids_emails) > max_emails else ids_emails
            
            for email_id in ids_emails:
                try:
                    # BODY.PEEK[] : ne marque pas l'email comme lu
                    status, data = self.connexion.uid("fetch", email_id, "(BODY.PEEK[])")
                    if status != "OK" or not data or not isinstance(data[0], tuple):
                        continue

                    message = email.message_from_bytes(data[0][1])

                    expediteur = self._decoder_expediteur(message.get("From", ""))
                    email_exp = self._extraire_email_expediteur(expediteur)
                    sujet = self._decoder_sujet(message.get("Subject", ""))
                    date = message.get("Date", "")
                    uid = email_id.decode() if isinstance(email_id, bytes) else str(email_id)

                    pieces_jointes = []

                    for numero, partie in enumerate(message.walk()):
                        # Certains clients envoient les PJ en "inline" : on se fie au nom de fichier
                        if partie.get_content_maintype() == "multipart":
                            continue
                        nom_fichier = partie.get_filename()
                        if not nom_fichier:
                            continue

                        nom_decoded = self._decoder_sujet(nom_fichier)
                        nom_decoded = self._nettoyer_nom_fichier(nom_decoded)

                        ext = os.path.splitext(nom_decoded)[1].lower()
                        if ext in ['.pdf', '.docx', '.doc']:
                            contenu = partie.get_payload(decode=True)
                            if contenu:
                                # Nom stable (UID + n° de partie) : pas de doublon ni d'écrasement
                                nom_sauvegarde = f"{uid}_{numero}_{nom_decoded}"
                                chemin_sauvegarde = os.path.join(self.dossier_local, nom_sauvegarde)

                                if not os.path.exists(chemin_sauvegarde):
                                    with open(chemin_sauvegarde, 'wb') as f:
                                        f.write(contenu)

                                pieces_jointes.append({
                                    'nom_original': nom_decoded,
                                    'nom_sauvegarde': nom_sauvegarde,
                                    'chemin': chemin_sauvegarde,
                                    'taille': len(contenu)
                                })
                    
                    if pieces_jointes:
                        emails_trouves.append({
                            'id': uid,
                            'expediteur': expediteur,
                            'email_expediteur': email_exp,
                            'sujet': sujet,
                            'date': date,
                            'pieces_jointes': pieces_jointes,
                            'nb_cv': len(pieces_jointes)
                        })
                
                except Exception as e:
                    print(f"Erreur traitement email {email_id}: {e}")
                    continue
            
            return emails_trouves, f"{len(emails_trouves)} email(s) avec CV trouvé(s)"
        
        except Exception as e:
            return [], f"Erreur : {str(e)}"
    
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