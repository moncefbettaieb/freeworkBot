import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import asyncio
import telegram
from telegram import Bot

# Configuration de la base de données SQLite
def init_db():
    conn = sqlite3.connect('job_offers.db')
    cursor = conn.cursor()
    cursor.execute('drop table if exists offers.db')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    return conn

# Fonction pour envoyer un email
def send_email(subject, body, password):
    sender_email = "moncefbettaieb@gmail.com"
    receiver_email = "mbettaieb@gcdconsulting.fr"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com')
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        logger_info.info(f"'{subject}' envoyé par mail avec succées.")
        print(f"'{subject}' envoyé par mail avec succées.")
    except Exception as e:
        logger_error.error(f"Echec de l'envoi de mail: {str(e)}")
        print(f"Echec de l'envoi de mail: {str(e)}")

def envoyer_message_telegram(bot_token, chat_id, message):
    try:
        bot = telegram.Bot(token=bot_token)
        bot = Bot(token = bot_token)
        asyncio.run(bot.send_message(chat_id=chat_id, text=message))
        logger_info.info(f"Message '{message}' eenvoyé avec succès.")
        print(f"Message '{message}' envoyé avec succès.")
    except telegram.error.TelegramError as e:
        print(f"Une erreur s'est produite avec Telegram: {e}")
    except Exception as e:
        logger_error.error(f"Echec de l'envoi du message Telegram: {str(e)}")
        print(f"Une autre erreur s'est produite: {e}")

def fetchOffer(url):
# URL de la page que vous souhaitez scraper

    # Initialiser la base de données
    conn = init_db()
    cursor = conn.cursor()

    # Faire une requête GET pour récupérer le contenu de la page
    response = requests.get(url)

    # Vérifier si la requête a été réussie
    if response.status_code == 200:
        # Parser le contenu de la page avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Trouver tous les éléments qui correspondent aux titres des offres
        job_titles = soup.find_all('a', class_='after:absolute after:inset-0')

        # Traiter chaque offre
        for job in job_titles:
            title = job.get_text(strip=True)
            link = "https://www.free-work.com" + job['href']

            # Vérifier si l'offre existe déjà dans la base de données
            cursor.execute("SELECT * FROM offers WHERE link=?", (link,))
            result = cursor.fetchone()

            if result is None:
                # Envoyer un email
                subject = "Nouvelle offre d'emploi : " + title
                body = f"Une nouvelle offre d'emploi a été trouvée :\n\nTitre: {title}\nLien: {link}"
                send_email(subject, body, app_mail_password)
                envoyer_message_telegram(BOT_TOKEN, CHAT_ID, body)
                #send_whatsApp(body)
                # Si l'offre n'existe pas, l'ajouter à la base de données
                cursor.execute("INSERT INTO offers (title, link) VALUES (?, ?)", (title, link))
                conn.commit()
            else:
                logger_info.info(f"L'offre '{title}' existe déjà dans la base de données.")
                print(f"L'offre '{title}' existe déjà dans la base de données.")

    # Fermer la connexion à la base de données
    conn.close()

# Créer des loggers
logger_info = logging.getLogger('info_logger')
logger_error = logging.getLogger('error_logger')

# Définir le niveau des loggers
logger_info.setLevel(logging.INFO)
logger_error.setLevel(logging.ERROR)

# Créer des handlers (gestionnaires de log)
info_handler = logging.FileHandler('logs/info.log')
error_handler = logging.FileHandler('logs/error.log')

# Définir le niveau des handlers
info_handler.setLevel(logging.INFO)
error_handler.setLevel(logging.ERROR)

# Créer un formatter (pour le format des messages de log)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Associer le formatter aux handlers
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Ajouter les handlers aux loggers
logger_info.addHandler(info_handler)
logger_error.addHandler(error_handler)


def main():
    urls = [
    "https://www.free-work.com/fr/tech-it/jobs?query=data%20engineer&contracts=contractor&sort=date",
    "https://www.free-work.com/fr/tech-it/jobs?query=gcp&contracts=contractor&sort=date",
    "https://www.free-work.com/fr/tech-it/jobs?query=Data%20engineer&remote=full&sort=date",
    "https://www.free-work.com/fr/tech-it/jobs?query=spark&contracts=contractor&sort=date",
    "https://www.free-work.com/fr/tech-it/jobs?query=snowflake&contracts=contractor&sort=date"
]

    # Parcourir le tableau d'URLs
    for url in urls:
        fetchOffer(url)

if __name__ == "__main__":
    # Récupérer le mot de passe 
    load_dotenv()
    app_mail_password = os.getenv('APP_MAIL_PASSWORD')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    print(BOT_TOKEN)
    CHAT_ID = '1127653878'  # ID de la conversation (peut être trouvé via @userinfobot)
    main()