import time
import requests
import feedparser
import os # Nécessaire pour lire la variable d'environnement (le secret)

# --- 🛠️ CONFIGURATION (VOS IDENTIFIANTS) ---
# Jeton d'API de votre bot : Ce code va lire le secret BOT_TOKEN de GitHub/Replit.
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Identifiant de votre canal : https://t.me/REALMADRIDNEWS0001
CANAL_ID = '@REALMADRIDNEWS0001'

# 🌐 Nouvelle Source d'actualités du Real Madrid (Flux RSS en FRANÇAIS)
SOURCE_RSS_URL = 'https://www.lequipe.fr/rss/actu_real-madrid.xml'

# Fichier pour stocker les liens des articles déjà publiés (pour éviter les doublons)
LOG_FILE = 'published_links.txt' 

# Temps d'attente entre chaque vérification (en secondes) : 5 minutes
WAIT_TIME_SECONDS = 300 
# --- FIN CONFIGURATION ---


def charger_liens_publies(fichier):
    """Charge les liens déjà publiés depuis un fichier texte."""
    try:
        with open(fichier, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def sauvegarder_lien_publie(fichier, lien):
    """Ajoute un nouveau lien au fichier."""
    with open(fichier, 'a') as f:
        f.write(f"{lien}\n")


def obtenir_nouvelles_via_rss():
    """
    Se connecte au flux RSS FRANCOPHONE, analyse et récupère les nouvelles.
    """
    print("Vérification des nouvelles sur le flux RSS francophone...")
    nouvelles = []
    
    try:
        # Utilisation de feedparser pour lire le flux RSS
        feed = feedparser.parse(SOURCE_RSS_URL)
        
        for entry in feed.entries:
            # Nettoyage du titre
            titre = entry.title.replace('*', '').replace('_', '').strip()
            
            # Utilisation de 'summary' ou 'description' pour le résumé
            texte = entry.summary if 'summary' in entry else entry.get('description', 'Résumé non disponible.')
            lien = entry.link
            
            # Nettoyage simple du texte (enlève le HTML initial)
            cleaned_text = texte.split('<')[0].strip()
            
            if not lien or not titre:
                continue
                
            nouvelles.append({
                'titre': titre,
                'texte': cleaned_text, 
                'lien': lien
            })
            
    except Exception as e:
        print(f"Erreur lors de la lecture du flux RSS : {e}")
        
    return nouvelles

def publier_sur_telegram(nouvelle):
    """
    Envoie le message formaté au canal Telegram.
    """
    # Vérification essentielle : si le jeton n'est pas chargé (erreur de secret), on arrête
    if not BOT_TOKEN:
        print("Erreur: Le BOT_TOKEN n'a pas été chargé depuis les secrets de l'environnement.")
        return False

    message_texte = (
        f"⚽️ <b>{nouvelle['titre']}</b>\n\n"
        f"{nouvelle['texte']}\n\n"
        f"📰 <b>Source :</b> <a href=\"{nouvelle['lien']}\">Lire l'article complet</a>"
    )
    
    # URL de l'API pour envoyer un message
    api_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    
    payload = {
        'chat_id': CANAL_ID,
        'text': message_texte,
        'parse_mode': 'HTML', # Utilisation de HTML pour les balises (<b> pour le gras)
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(api_url, data=payload)
        response.raise_for_status()
        
        if response.json().get('ok'):
            return True
        else:
            print(f"Erreur API Telegram : {response.json().get('description')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion à l'API Telegram : {e}")
        return False


def bot_loop():
    """
    La boucle principale qui tourne 24/24.
    """
    articles_publies = charger_liens_publies(LOG_FILE)
    print(f"Démarrage. {len(articles_publies)} articles déjà connus. Vérification 24/24 active.")
    
    while True:
        try:
            nouvelles_trouvees = obtenir_nouvelles_via_rss()
            nouvelles_a_traiter = reversed(nouvelles_trouvees) 
            
            for nouvelle in nouvelles_a_traiter:
                nouvelle_id = nouvelle['lien'] 
                
                if nouvelle_id not in articles_publies:
                    print(f"✅ Nouvelle information trouvée : {nouvelle['titre']}")
                    
                    if publier_sur_telegram(nouvelle):
                        articles_publies.add(nouvelle_id)
                        sauvegarder_lien_publie(LOG_FILE, nouvelle_id)
                        print("    -> Publication réussie.")
                        time.sleep(5) 
                    else:
                        print("    -> Échec de la publication.")
                
        except Exception as e:
            print(f"❌ Erreur critique dans la boucle : {e}")
            
        print(f"\n--- Attente de {WAIT_TIME_SECONDS / 60} minutes ---\n")
        time.sleep(WAIT_TIME_SECONDS) 

# --- Exécution ---
if __name__ == "__main__":
    bot_loop()
