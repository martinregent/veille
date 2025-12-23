#!/usr/bin/env python3
"""
Serveur API local optionnel pour la veille technologique.
Permet à l'extension Chrome de communiquer via HTTP au lieu de l'API GitHub.

Usage:
    python3 scripts/veille_api_server.py

Endpoints:
    POST /api/capture - Capturer une URL
"""

import os
import sys
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Charger les variables d'environnement
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Importer les fonctions de traitement de process_veille
# On ajoute le dossier scripts au path pour permettre l'import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from process_veille import (
        scrape_content, 
        analyze_with_mistral, 
        create_markdown_fiche, 
        update_index_page
    )
except ImportError as e:
    print(f"⚠️ Erreur import process_veille: {e}")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_USER = os.getenv("GITHUB_USER", "martinregent").strip()
REPO_NAME = os.getenv("REPO_NAME", "veille").strip()

class VeilleAPIHandler(BaseHTTPRequestHandler):
    """Gestionnaire HTTP pour l'API Veille"""

    def do_POST(self):
        """Gère les requêtes POST"""
        if self.path == '/api/capture':
            self.handle_capture()
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        """Gère les requêtes OPTIONS (CORS preflight)"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_capture(self):
        """Endpoint: Capturer une URL"""
        try:
            # Lire le corps de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Valider les données
            url = data.get('url')
            if not url:
                return self.send_json_error(400, "URL manquante")

            description = data.get('description', '')
            tags = data.get('tags', [])

            print(f"📥 Capture reçue: {url}")

            # 1. Créer l'issue GitHub (pour le déploiement Cloudflare)
            try:
                issue = self.create_github_issue(url, description, tags)
                issue_number = issue['number']
                print(f"   ✅ Issue GitHub #{issue_number} créée")
            except Exception as e:
                print(f"   ⚠️ Erreur GitHub sync: {e}")
                issue_number = 0

            # 2. Traitement Local Temps Réel
            print(f"   ⚙️ Traitement local en cours...")
            content, image_url = scrape_content(url)
            local_success = False
            if content:
                analysis = analyze_with_mistral(content, url, description, tags)
                if analysis:
                    if create_markdown_fiche(analysis, url, issue_number, image_url):
                        update_index_page()
                        print(f"   ✨ Fiche locale créée et index mis à jour")
                        local_success = True
                    else:
                        print(f"   ❌ Erreur création fiche locale")
                else:
                    print(f"   ❌ Erreur analyse Mistral")
            else:
                print(f"   ❌ Erreur scraping contenu")

            if local_success:
                msg = "Article capturé et traité localement"
            else:
                msg = "Article capturé mais erreur lors du traitement local"

            # Retourner la réponse
            self.send_json_response(200, {
                'status': 'success',
                'message': msg,
                'issue_number': issue_number
            })

        except json.JSONDecodeError:
            self.send_json_error(400, "JSON invalide")
        except Exception as e:
            print(f"   ❌ Erreur serveur: {e}")
            self.send_json_error(500, str(e))

    def create_github_issue(self, url, description, tags):
        """Crée une issue GitHub"""
        if not GITHUB_TOKEN:
            raise Exception("GITHUB_TOKEN non configuré")

        # Préparer le contenu de l'issue (Format JSON pour process_veille)
        issue_data = {
            "url": url,
            "note": description,
            "tags": tags
        }
        body = json.dumps(issue_data, indent=2)

        # Préparer les labels
        labels = ['to_process']

        # Faire la requête GitHub
        response = requests.post(
            f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/issues",
            headers={
                'Authorization': f"token {GITHUB_TOKEN}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            json={
                'title': 'Article à traiter',
                'body': body,
                'labels': labels
            },
            timeout=10
        )

        if response.status_code != 201:
            error_data = response.json()
            raise Exception(f"Erreur GitHub: {error_data.get('message', 'Unknown error')}")

        return response.json()

    def send_json_response(self, status_code, data):
        """Envoie une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_json_error(self, status_code, error_message):
        """Envoie une erreur JSON"""
        self.send_json_response(status_code, {
            'status': 'error',
            'error': error_message
        })

    def log_message(self, format, *args):
        """Override pour des logs custom"""
        print(f"[{self.client_address[0]}] {format % args}")


def run_server(host='localhost', port=5888):
    """Lance le serveur HTTP"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, VeilleAPIHandler)

    print(f"""
╔════════════════════════════════════════════════╗
║         🚀 Veille API Server démarré            ║
╠════════════════════════════════════════════════╣
║ URL:     http://{host}:{port}               ║
║ Endpoint: POST http://{host}:{port}/api/capture ║
╠════════════════════════════════════════════════╣
║ Configuration:                                  ║
║ • GitHub User: {GITHUB_USER:<25}║
║ • Repository:  {REPO_NAME:<25}║
║ • Token:       {"✅ Configuré" if GITHUB_TOKEN else "❌ Manquant":<25}║
╚════════════════════════════════════════════════╝

Exemple de requête:
    curl -X POST http://{host}:{port}/api/capture \\
         -H "Content-Type: application/json" \\
         -d '{{
           "url": "https://example.com/article",
           "description": "Une note personnelle",
           "tags": ["tag1", "tag2"]
         }}'

Appuie sur CTRL+C pour arrêter.
""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Serveur arrêté.")
        httpd.server_close()


if __name__ == '__main__':
    # Valider la configuration
    if not GITHUB_TOKEN:
        print("❌ ERREUR: GITHUB_TOKEN non défini dans .env")
        sys.exit(1)

    # Lancer le serveur
    run_server()
