from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Authentification requirements
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
from playlist_update.config import TOKEN_FILE, CREDENTIALS_FILE


def get_authenticated_service():
    """
    Gère le cycle de vie du jeton OAuth 2.0 (génération, stockage, rafraîchissement).
    Retourne l'objet ressource 'youtube' prêt à l'emploi.
    """
    creds = None
    
    # 1. Tentative de chargement du token existant
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            print("[AUTH] Fichier token corrompu ou invalide. Nouvelle authentification requise...")
            creds = None
    
    # 2. Si le token est invalide ou inexistant
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[AUTH] Rafraîchissement du jeton expiré...")
                creds.refresh(Request())
            except Exception:
                print("[AUTH] Refresh token invalide. Nouvelle authentification requise...")
                creds = None  # Force le flux OAuth complet
        
        # Si refresh a échoué (creds = None) ou si pas de token, lancer flux OAuth
        if not creds:
            print("[AUTH] Initiation du flux d'authentification OAuth...")
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"Le fichier '{CREDENTIALS_FILE}' est manquant.")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Port fixe 8080 pour correspondre à la console Google Cloud
            creds = flow.run_local_server(port=8080)
        
        # 3. Sauvegarde du nouveau token (Persistance)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)
