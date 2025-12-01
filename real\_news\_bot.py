import time
import requests
import feedparser

# --- 🛠️ CONFIGURATION (VOS IDENTIFIANTS) ---
# Jeton d'API de votre bot : https://t.me/RMNews247Bot
BOT_TOKEN = '8323375048:AAH2-tspVlABm2QgxkxKGIkhlDXaQSqploA'

# Identifiant de votre canal : https://t.me/REALMADRIDNEWS0001
CANAL_ID = '@REALMADRIDNEWS0001'

# 🌐 NOUVELLE Source d'actualités du Real Madrid (Flux RSS en FRANÇAIS, FONCTIONNEL)
SOURCE_RSS_URL = 'https://www.dailymercato.com/club/real-madrid-5/rss'

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
    # Note : Dans un environnement comme Replit, ce fichier est stocké localement.
    with open(fichier, 'a') as f:
        f.write(f"{lien}\n")


def obtenir_nouvelles_via_rss():
    """
    TEST UNIQUEMENT : Retourne un article de test pour vérifier la connexion Telegram.
    REMETTEZ LE CODE INITIAL APRES LE TEST.
    """
    # Ce dictionnaire simule un article trouvé par le flux RSS
    article_test = {
        'titre': "✅ TEST RÉUSSI : Connexion Telegram OK !",
        'texte': "Ceci est un message de test automatique. Le bot est bien administrateur et peut poster sur le canal. La publication va se lancer maintenant.", 
        # Utiliser un lien unique pour ce test
        'lien': 'https://test.realnewsbot.com/' + str(time.time()) 
    }
    
    # On renvoie l'article de test dans une liste
    return [article_test]

def publier_sur_telegram(nouvelle):
    """
    Étape 2 : Envoie le message formaté au canal Telegram.
    """
    
    # Construction du texte du message avec le formatage HTML pour le lien et le gras.
    
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
    Étape 3 : La boucle principale qui tourne 24/24.
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
