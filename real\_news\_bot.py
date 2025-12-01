import time
import requests
import feedparser

# --- 🛠️ CONFIGURATION (VOS IDENTIFIANTS) ---
# Jeton d'API de votre bot :
BOT_TOKEN = '8323375048:AAH2-tspVlABm2QgxkxKGIkhlDXaQSqploA'

# Identifiant de votre canal :
CANAL_ID = '@REALMADRIDNEWS0001'

# 🌐 SOURCE DÉFINITIVE (Francophone et Fonctionnelle)
SOURCE_RSS_URL = 'https://www.dailymercato.com/club/real-madrid-5/rss'

# Fichier pour stocker les liens des articles déjà publiés 
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
    """Ajoute un nouveau lien au fichier log."""
    with open(fichier, 'a') as f:
        f.write(f"{lien}\n")


def obtenir_nouvelles_via_rss():
    """
    Se connecte au flux RSS fonctionnel, analyse et récupère les nouvelles.
    """
    print("Vérification des nouvelles sur le flux RSS francophone...")
    nouvelles = []
    
    try:
        feed = feedparser.parse(SOURCE_RSS_URL)
        
        for entry in feed.entries:
            titre = entry.title.replace('*', '').replace('_', '').strip()
            
            texte = entry.summary if 'summary' in entry else entry.get('description', 'Résumé non disponible.')
            lien = entry.link
            
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
    
    message_texte = (
        f"⚽️ <b>{nouvelle['titre']}</b>\n\n"
        f"{nouvelle['texte']}\n\n"
        f"📰 <b>Source :</b> <a href=\"{nouvelle['lien']}\">Lire l'article complet</a>"
    )
    
    api_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    
    payload = {
        'chat_id': CANAL_ID,
        'text': message_texte,
        'parse_mode': 'HTML',
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
            # On inverse l'ordre pour s'assurer de traiter les plus récents en dernier
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
