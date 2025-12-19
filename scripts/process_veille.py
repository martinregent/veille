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
from mistralai.client import MistralClient
import yaml
from dotenv import load_dotenv
import trafilatura

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

def extract_issue_data(issue_body):
    """
    Extrait les données de l'issue (URL, note, tags).
    Supporte le format JSON ou le format URL simple.
    """
    issue_body = issue_body.strip()
    
    # Essayer de parser comme JSON
    try:
        if issue_body.startswith('{'):
            data = json.loads(issue_body)
            return {
                "url": data.get("url"),
                "note": data.get("note", ""),
                "user_tags": data.get("tags", [])
            }
    except json.JSONDecodeError:
        pass
    
    # Format fallback: première ligne est l'URL
    lines = issue_body.split('\n')
    url = lines[0].strip()
    return {
        "url": url if url.startswith(('http://', 'https://')) else None,
        "note": "",
        "user_tags": []
    }

def scrape_content(url):
    """Scrape le contenu textuel et l'image d'une URL via Trafilatura."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"   ⚠️  Trafilatura: Échec du téléchargement pour {url}")
            return None, None

        # Extraction du texte principal
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=True, no_fallback=False)
        
        # Extraction des métadonnées pour l'image
        metadata = trafilatura.extract_metadata(downloaded)
        image_url = metadata.image if metadata and metadata.image else None

        if not text:
             print(f"   ⚠️  Trafilatura: Pas de texte extrait pour {url}")
             return None, None

        # Limiter la taille pour ne pas exploser le contexte Mistral
        if len(text) > 25000:
            text = text[:25000] + "..."

        return text, image_url

    except Exception as e:
        print(f"   ⚠️  Erreur scraping {url}: {e}")
        return None, None

def analyze_with_mistral(text, url, user_note="", user_tags=[]):
    """Analyse le texte avec Mistral et retourne un JSON structuré."""
    client = MistralClient(api_key=MISTRAL_API_KEY)

    user_context = ""
    if user_note:
        user_context += f"\nNote de l'utilisateur sur cet article : {user_note}"
    if user_tags:
        user_context += f"\nTags suggérés par l'utilisateur : {', '.join(user_tags)}"

    prompt = f"""Analyse le texte suivant qui provient d'un article technique pour une veille technologique.

INSTRUCTIONS IMPORTANTES:
- Réponds UNIQUEMENT en JSON valide (pas de texte avant ou après)
- Ne modifie pas la structure JSON proposée
- Assure-toi que le JSON est parsable
- Les tags doivent être pertinents et courts. Inclus les tags suggérés par l'utilisateur si pertinents.
- La thématique doit être UNE SEULE parmi: [DevOps, IA & Data, Développement, Architecture, Business, Cybersécurité, Infrastructure]
- Le résumé doit faire entre 300-500 mots.
- Intègre la note de l'utilisateur dans le résumé si elle apporte du contexte.

Format JSON attendu:
{{
    "titre": "Titre pertinent en français",
    "resume": "Résumé détaillé du contenu...",
    "tags": ["tag1", "tag2", "tag3"],
    "thematique": "Nom de la thématique"
}}

{user_context}

Texte à analyser:
{text}

---
Source: {url}
"""

    try:
        chat_response = client.chat(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = chat_response.choices[0].message.content.strip()

        # Essayer de parser le JSON
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

def create_markdown_fiche(data, url, issue_number, image_url=None):
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
    
    if image_url:
        frontmatter["image"] = image_url

    content = f"""---
{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---

# {data['titre']}

*Source : [{url}]({url})*

"""

    if image_url:
        content += f"![Image principale]({image_url})\n\n"

    content += f"""## Résumé

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
        issue_body = issue['body'] or ""
        
        # Extraction des données structurées
        data = extract_issue_data(issue_body)
        url = data['url']
        note = data['note']
        user_tags = data['user_tags']

        if not url:
            print(f"[{idx}/{len(issues)}] Issue #{issue_number}: ❌ Pas d'URL valide")
            add_issue_comment(
                issue_number,
                "❌ Erreur: L'issue ne contient pas d'URL valide."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        print(f"[{idx}/{len(issues)}] Issue #{issue_number}: {url[:60]}")

        # Scraper le contenu avec Trafilatura
        content, image_url = scrape_content(url)
        if not content:
            print(f"   ⚠️  Impossible de scraper le contenu")
            add_issue_comment(
                issue_number,
                "⚠️ Erreur: Impossible de récupérer le contenu de l'URL. L'URL est peut-être invalide, protégée ou inaccessible."
            )
            close_issue(issue_number)
            error_count += 1
            continue

        # Analyser avec Mistral
        analysis = analyze_with_mistral(content, url, note, user_tags)
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
        if create_markdown_fiche(analysis, url, issue_number, image_url):
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
