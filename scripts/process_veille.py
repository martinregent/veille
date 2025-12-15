#!/usr/bin/env python3
"""
Script de traitement automatisé pour la veille technologique.
Récupère les issues GitHub, scrape le contenu, utilise Mistral pour l'analyse,
et génère les fiches Markdown.
"""

import os
import sys
import requests
import datetime
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from mistralai import Mistral
import yaml
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_USER = os.getenv("GITHUB_USER", "martinregent").strip()
REPO_NAME = os.getenv("REPO_NAME", "veille").strip()

# Validation des clés
if not MISTRAL_API_KEY:
    print("❌ ERREUR: MISTRAL_API_KEY non définie dans .env")
    sys.exit(1)

if not GITHUB_TOKEN:
    print("❌ ERREUR: GITHUB_TOKEN non défini dans .env")
    sys.exit(1)

# --- FONCTIONS ---

def get_open_issues():
    """Récupère les issues GitHub avec le label 'to_process'."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/issues"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {"labels": "to_process", "state": "open", "per_page": 100}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"❌ Erreur API GitHub: {resp.status_code}")
            print(f"   {resp.text}")
            return []
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des issues: {e}")
        return []

def scrape_content(url):
    """Scrape le contenu textuel d'une URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Nettoyage basique (supprimer scripts, styles, nav, footer)
        for script in soup(["script", "style", "nav", "footer", "noscript"]):
            script.decompose()

        text = soup.get_text(separator=' ')
        # Réduire les espaces multiples
        clean_text = re.sub(r'\s+', ' ', text).strip()

        # Limiter la taille pour ne pas exploser le contexte Mistral
        if len(clean_text) > 15000:
            clean_text = clean_text[:15000] + "..."

        return clean_text if clean_text else None
    except Exception as e:
        print(f"   ⚠️  Erreur scraping {url}: {e}")
        return None

def analyze_with_mistral(text, url):
    """Analyse le texte avec Mistral et retourne un JSON structuré."""
    client = Mistral(api_key=MISTRAL_API_KEY)

    prompt = f"""Analyse le texte suivant qui provient d'un article technique pour une veille technologique.

INSTRUCTIONS IMPORTANTES:
- Réponds UNIQUEMENT en JSON valide (pas de texte avant ou après)
- Ne modifie pas la structure JSON proposée
- Assure-toi que le JSON est parsable
- Les tags doivent être pertinents et courts
- La thématique doit être UNE SEULE parmi: [DevOps, IA & Data, Développement, Architecture, Business, Cybersécurité, Infrastructure]
- Le résumé doit faire entre 300-500 mots

Format JSON attendu:
{{
    "titre": "Titre pertinent en français",
    "resume": "Résumé détaillé du contenu...",
    "tags": ["tag1", "tag2", "tag3"],
    "thematique": "Nom de la thématique"
}}

Texte à analyser:
{text}

---
Source: {url}
"""

    try:
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = chat_response.choices[0].message.content.strip()

        # Essayer de parser le JSON
        # Parfois Mistral ajoute du texte avant/après, on cherche le JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()

        data = json.loads(response_text)

        # Validation minimale
        required_keys = {"titre", "resume", "tags", "thematique"}
        if not all(key in data for key in required_keys):
            print(f"   ⚠️  Clés manquantes dans la réponse Mistral")
            return None

        return data
    except json.JSONDecodeError as e:
        print(f"   ⚠️  Erreur parsing JSON Mistral: {e}")
        print(f"   Réponse: {response_text[:200]}...")
        return None
    except Exception as e:
        print(f"   ⚠️  Erreur Mistral: {e}")
        return None

def create_markdown_fiche(data, url, issue_number):
    """Crée le fichier Markdown de la fiche."""
    date_now = datetime.datetime.now()
    year = date_now.strftime("%Y")
    month = date_now.strftime("%m")
    day = date_now.strftime("%d")

    # Création du dossier docs/fiches/YYYY/MM
    base_path = Path("docs/fiches") / year / month
    base_path.mkdir(parents=True, exist_ok=True)

    # Génération du slug pour le nom du fichier
    safe_title = re.sub(r'[^a-z0-9]+', '-', data['titre'].lower()).strip('-')
    filename = base_path / f"{day}-{safe_title}.md"

    # Frontmatter YAML pour MkDocs
    frontmatter = {
        "title": data['titre'],
        "tags": data['tags'],
        "category": data['thematique'],
        "date": date_now.strftime("%Y-%m-%d"),
        "source": url,
        "issue": f"#{issue_number}"
    }

    content = f"""---
{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---

# {data['titre']}

*Source : [{url}]({url})*

## Résumé

{data['resume']}

---

**Thématique :** {data['thematique']}

**Tags :** {', '.join([f'`{tag}`' for tag in data['tags']])}

*Généré automatiquement via Mistral AI - Issue {issue_number}*
"""

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ Fiche créée: {filename}")
        return True
    except Exception as e:
        print(f"   ❌ Erreur création fichier: {e}")
        return False

def close_issue(issue_number):
    """Ferme une issue GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/issues/{issue_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        resp = requests.patch(url, headers=headers, json={"state": "closed"}, timeout=10)
        if resp.status_code == 200:
            print(f"   🔒 Issue #{issue_number} fermée")
            return True
        else:
            print(f"   ⚠️  Erreur fermeture issue: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️  Erreur fermeture issue: {e}")
        return False

def add_issue_comment(issue_number, comment):
    """Ajoute un commentaire à une issue."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/issues/{issue_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={"body": comment},
            timeout=10
        )
        return resp.status_code == 201
    except Exception as e:
        print(f"   ⚠️  Erreur ajout commentaire: {e}")
        return False

# --- MAIN ---

def main():
    """Boucle principale du traitement."""
    print("\n🚀 Démarrage du traitement de la veille...\n")

    # Récupérer les issues
    issues = get_open_issues()
    if not issues:
        print("ℹ️  Aucune issue à traiter.")
        return

    print(f"🔍 {len(issues)} lien(s) à traiter...\n")

    success_count = 0
    error_count = 0

    for idx, issue in enumerate(issues, 1):
        issue_number = issue['number']
        url = issue['body'].strip() if issue['body'] else None

        if not url:
            print(f"[{idx}/{len(issues)}] Issue #{issue_number}: ❌ Pas d'URL")
            add_issue_comment(
                issue_number,
                "❌ Erreur: L'issue ne contient pas d'URL valide dans la description."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        # Valider que c'est une URL
        if not url.startswith(('http://', 'https://')):
            print(f"[{idx}/{len(issues)}] Issue #{issue_number}: ❌ URL invalide: {url[:50]}")
            add_issue_comment(
                issue_number,
                f"❌ Erreur: '{url}' n'est pas une URL valide."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        print(f"[{idx}/{len(issues)}] Issue #{issue_number}: {url[:60]}")

        # Scraper le contenu
        content = scrape_content(url)
        if not content:
            print(f"   ⚠️  Impossible de scraper le contenu")
            add_issue_comment(
                issue_number,
                "⚠️ Erreur: Impossible de récupérer le contenu de l'URL. L'URL est peut-être invalide ou inaccessible."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        # Analyser avec Mistral
        analysis = analyze_with_mistral(content, url)
        if not analysis:
            print(f"   ⚠️  Erreur analyse Mistral")
            add_issue_comment(
                issue_number,
                "⚠️ Erreur: Impossible d'analyser le contenu avec Mistral."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        # Créer la fiche Markdown
        if create_markdown_fiche(analysis, url, issue_number):
            # Ajouter un commentaire de succès
            add_issue_comment(
                issue_number,
                f"""✅ Fiche créée avec succès!

**Titre:** {analysis['titre']}

**Thématique:** {analysis['thematique']}

**Tags:** {', '.join(analysis['tags'])}

*Fiche générée et publiée automatiquement.*"""
            )
            close_issue(issue_number)
            success_count += 1
        else:
            error_count += 1

    # Résumé
    print(f"\n{'='*50}")
    print(f"✅ Succès: {success_count}")
    print(f"❌ Erreurs: {error_count}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
