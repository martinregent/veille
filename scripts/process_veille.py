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
import yaml
from dotenv import load_dotenv
# trafilatura supprimé car incompatible avec Python 3.14


# Charger les variables d'environnement
# On cherche le .env à la racine du projet
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_USER = os.getenv("GITHUB_USER", "martinregent").strip()
REPO_NAME = os.getenv("REPO_NAME", "veille").strip()

# --- PATHS ---
# Définir la racine du projet de manière absolue
# PROJECT_ROOT déjà défini au dessus pour load_dotenv
DOCS_DIR = PROJECT_ROOT / "docs"
FICHES_DIR = DOCS_DIR / "fiches"

# Validation des clés
if not MISTRAL_API_KEY:
    print("❌ ERREUR: MISTRAL_API_KEY non définie dans .env")
    sys.exit(1)

if not GITHUB_TOKEN:
    print("❌ ERREUR: GITHUB_TOKEN non défini dans .env")
    sys.exit(1)

# --- FONCTIONS ---

def get_open_issues():
    """Récupère les issues GitHub à traiter (label 'to_process' ou titre spécifique)."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/issues"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    # On récupère toutes les issues ouvertes sans filtrer par label ici
    params = {"state": "open", "per_page": 100}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            all_issues = resp.json()
            # Filtrage côté client : Label 'to_process' OU Titre 'Article à traiter'
            filtered_issues = [
                i for i in all_issues
                if any(l['name'] == 'to_process' for l in i['labels']) or
                "Article à traiter" in i['title']
            ]
            return filtered_issues
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
    
    # Format fallback: Recherche d'une URL dans le texte (supporte markdown, texte brut, etc.)
    # Cherche http:// ou https:// suivi de caractères non-espaces et non ')]'
    url_match = re.search(r'(https?://[^\s)\]"]+)', issue_body)
    
    if url_match:
        url = url_match.group(1)
    else:
        # Si rien trouvé, on tente la première ligne nettoyée
        lines = issue_body.split('\n')
        url = lines[0].strip()

    return {
        "url": url if url and url.startswith(('http://', 'https://')) else None,
        "note": "",
        "user_tags": []
    }

def scrape_content(url):
    """Scrape le contenu textuel et l'image d'une URL via BeautifulSoup."""
    from bs4 import BeautifulSoup
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraction de l'image og:image
        og_image = soup.find("meta", property="og:image")
        image_url = og_image["content"] if og_image else None

        # Nettoyage basique (supprimer scripts, styles, nav, footer)
        for script in soup(["script", "style", "nav", "footer", "noscript", "header"]):
            script.decompose()

        text = soup.get_text(separator=' ')
        # Réduire les espaces multiples
        clean_text = re.sub(r'\s+', ' ', text).strip()

        if not clean_text:
             return None, None

        # Limiter la taille pour ne pas exploser le contexte Mistral
        if len(clean_text) > 15000:
            clean_text = clean_text[:15000] + "..."

        return clean_text, image_url

    except Exception as e:
        print(f"   ⚠️  Erreur scraping {url}: {e}")
        return None, None

def analyze_with_mistral(text, url, user_note="", user_tags=[]):
    """Analyse le texte avec Mistral et retourne un JSON structuré."""
    from mistralai.client import MistralClient
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

        try:
            # strict=False autorise les sauts de ligne dans les chaînes (common LLM issue)
            data = json.loads(response_text, strict=False)
        except json.JSONDecodeError:
            # Fallback : tentative de nettoyage des sauts de ligne non échappés
            clean_text = response_text.replace('\n', ' ').replace('\r', '')
            data = json.loads(clean_text, strict=False)

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
    base_path = FICHES_DIR / year / month
    base_path.mkdir(parents=True, exist_ok=True)

    # Génération du slug pour le nom du fichier
    # On remplace les accents et caractères spéciaux pour un slug propre
    def slugify(text):
        text = text.lower()
        # Remplacements de base pour le français
        replacements = {'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'à': 'a', 'â': 'a', 'î': 'i', 'ï': 'i', 'ô': 'o', 'û': 'u', 'ù': 'u', 'ç': 'c'}
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        # Tout ce qui n'est pas alphanumérique devient un tiret
        text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
        return text

    safe_title = slugify(data['titre'])
    filename = base_path / f"{day}-{safe_title}.md"

    # Frontmatter YAML pour MkDocs
    frontmatter = {
        "title": data['titre'],
        "tags": data['tags'],
        "category": data['thematique'],
        "date": date_now.date(),  # Objet date pour éviter les quotes dans le YAML
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

    # Tentative d'écriture
    try:
        # 1. Tentative standard
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ Fiche créée: {filename}")
            return True
        except PermissionError as e:
            print(f"   ⚠️ Échec écriture Python ({e}), tentative via Shell...")
            
            # 2. Repli via Shell (cat)
            import subprocess
            process = subprocess.Popen(['cat', '-', '>', str(filename)], stdin=subprocess.PIPE, shell=True)
            process.communicate(input=content.encode('utf-8'))
            
            if process.returncode == 0:
                print(f"   ✅ Fiche créée via Shell: {filename}")
                return True
            else:
                raise Exception(f"Shell return code: {process.returncode}")

    except Exception as e:
        print(f"   ❌ Erreur fatale création fiche: {e}")
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

def update_index_page():
    """Régénère la page d'accueil avec la liste chronologique des fiches."""
    if not FICHES_DIR.exists():
        return

    articles = []

    # Parcourir tous les fichiers markdown
    processed_titles = set()
    print(f"📂 Recherche de fiches dans: {FICHES_DIR}")
    for file_path in FICHES_DIR.rglob("*.md"):
        # Ignorer l'index lui-même
        if file_path.name == "index.md": continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extraction frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                    except Exception as e:
                        print(f"   ⚠️  Erreur YAML dans {file_path}: {e}")
                        continue
                        
                    title = fm.get('title', file_path.stem)
                    
                    # Dédoublonnage par titre (insensible à la casse)
                    case_title = title.lower().strip()
                    if case_title in processed_titles:
                        continue
                    processed_titles.add(case_title)
                    
                    date_val = fm.get('date')
                    
                    # Parsing robuste de la date
                    if isinstance(date_val, (datetime.date, datetime.datetime)):
                        date_obj = date_val if isinstance(date_val, datetime.date) else date_val.date()
                    elif isinstance(date_val, str):
                        try:
                            # Tente formats ISO YYYY-MM-DD
                            date_obj = datetime.datetime.strptime(date_val[:10], "%Y-%m-%d").date()
                        except:
                            date_obj = datetime.date.min
                    else:
                        date_obj = datetime.date.min
                    
                    # Chemin relatif pour le lien (MkDocs s'attend à un chemin relatif à la racine docs/)
                    rel_path = file_path.relative_to(DOCS_DIR)
                    
                    articles.append({
                        "date": date_obj,
                        "title": title,
                        "path": str(rel_path)
                    })
        except Exception as e:
            print(f"⚠️  Erreur lecture {file_path}: {e}")

    print(f"📊 {len(articles)} articles trouvés pour l'index.")

    # Trier par date décroissante puis titre
    articles.sort(key=lambda x: (x['date'], x['title']), reverse=True)

    # Générer le contenu de l'index
    index_content = """# 📰 Veille Technologique

## 📅 Derniers articles

"""

    current_month = None
    
    for art in articles:
        # En-tête de mois
        art_month = art['date'].strftime("%B %Y").capitalize() if art['date'] != datetime.date.min else "Anciens articles"
        if art_month != current_month:
            index_content += f"\n### {art_month}\n\n"
            current_month = art_month
            
        date_str = art['date'].strftime("%d/%m") if art['date'] != datetime.date.min else "??"
        index_content += f"- **[{date_str}]** [{art['title']}]({art['path']})\n"

    try:
        index_path = DOCS_DIR / "index.md"
        temp_path = DOCS_DIR / "index.md.tmp"
        
        # 1. Tentative d'écriture via temporaire + Shell replace (Workaround macOS EPERM)
        try:
            # Écrire dans un fichier temporaire
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            
            # Utiliser le shell pour le remplacement (cat) si os.replace échoue
            import subprocess
            cmd = f"cat {temp_path} > {index_path} && rm {temp_path}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"✅ Page d'accueil ({index_path}) mise à jour via Shell.")
            return
        except Exception as e:
            print(f"   ⚠️  Tentative Shell-cat échouée: {e}")
            # Ultime tentative standard
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            print("   ✅ Index mis à jour via écriture directe.")

    except Exception as e_final:
        print(f"❌ Échec définitif mise à jour index: {e_final}")

# --- MAIN ---

def main():
    """Boucle principale du traitement."""
    print("\n🚀 Démarrage du traitement de la veille...\n")

    # Récupérer les issues
    issues = get_open_issues()
    if not issues:
        print("ℹ️  Aucune issue à traiter.")
        # On met quand même à jour l'index au cas où il y a eu des modifs manuelles
        update_index_page()
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
    
    # Mise à jour de la page d'accueil
    update_index_page()

if __name__ == "__main__":
    main()
