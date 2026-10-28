# test_email.py
# Test de connexion à la boîte mail

from gestionnaire_email import tester_connexion

# Configuration (lue depuis secrets.toml)
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11 : pip install tomli

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

config = secrets["email"]

print("=" * 50)
print("🔌 Test de connexion IMAP")
print("=" * 50)
print(f"Serveur : {config['imap_server']}")
print(f"Port    : {config['imap_port']}")
print(f"Email   : {config['email_address']}")
print("=" * 50)

ok, msg = tester_connexion(
    config['imap_server'],
    config['imap_port'],
    config['email_address'],
    config['app_password']
)

print()
if ok:
    print(f"✅ SUCCÈS : {msg}")
else:
    print(f"❌ ÉCHEC : {msg}")