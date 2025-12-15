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
load_dotenv()

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
            if not data.get('url'):
                return self.send_json_error(400, "URL manquante")

            url = data.get('url')
            description = data.get('description', '')
            tags = data.get('tags', [])

            # Créer l'issue GitHub
            issue = self.create_github_issue(url, description, tags)

            # Retourner la réponse
            self.send_json_response(200, {
                'status': 'success',
                'message': f"Issue #{issue['number']} créée",
                'issue_url': issue['html_url'],
                'issue_number': issue['number']
            })

        except json.JSONDecodeError:
            self.send_json_error(400, "JSON invalide")
        except Exception as e:
            self.send_json_error(500, str(e))

    def create_github_issue(self, url, description, tags):
        """Crée une issue GitHub"""
        if not GITHUB_TOKEN:
            raise Exception("GITHUB_TOKEN non configuré")

        # Préparer le contenu de l'issue
        body = url
        if description:
            body += f"\n\n{description}"

        # Préparer les labels
        labels = ['to_process']
        if tags:
            labels.extend(tags[:3])  # Max 3 tags supplémentaires

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
