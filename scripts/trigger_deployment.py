#!/usr/bin/env python3
"""
Script pour déclencher manuellement le déploiement sur Cloudflare Pages
et la génération des fiches via GitHub Actions.

Usage:
    python3 scripts/trigger_deployment.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_USER = os.getenv("GITHUB_USER", "martinregent").strip()
REPO_NAME = os.getenv("REPO_NAME", "veille").strip()

def trigger_workflow():
    """Déclenche le workflow 'process-and-deploy.yml'"""
    if not GITHUB_TOKEN:
        print("❌ ERREUR: GITHUB_TOKEN non défini dans .env")
        sys.exit(1)

    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/actions/workflows/process-and-deploy.yml/dispatches"

    headers = {
        'Authorization': f"token {GITHUB_TOKEN}",
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

    payload = {
        'ref': 'main'
    }

    print(f"🚀 Déclenchement du workflow 'process-and-deploy.yml'...")
    print(f"   Repository: {GITHUB_USER}/{REPO_NAME}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ Workflow déclenché avec succès!")
            print(f"\n📊 Suivi: https://github.com/{GITHUB_USER}/{REPO_NAME}/actions")
            print(f"🌐 Site: https://veille.pages.dev")
            return True
        else:
            error_data = response.json()
            print(f"❌ Erreur: {response.status_code}")
            print(f"   Message: {error_data.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Erreur lors du déclenchement: {e}")
        return False

def get_workflow_runs():
    """Affiche les dernières exécutions du workflow"""
    if not GITHUB_TOKEN:
        return

    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/actions/workflows/process-and-deploy.yml/runs"

    headers = {
        'Authorization': f"token {GITHUB_TOKEN}",
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])

            if runs:
                print("\n📋 Dernières exécutions:")
                for run in runs[:5]:
                    status = run['status']
                    conclusion = run['conclusion'] or 'pending'
                    created = run['created_at'][:10]

                    status_icon = {
                        'completed': '✅' if conclusion == 'success' else '❌',
                        'in_progress': '⏳',
                        'queued': '⏳'
                    }.get(status, '❓')

                    print(f"   {status_icon} {created} - {status} ({conclusion})")
                    print(f"      {run['html_url']}")
            else:
                print("\n📋 Aucune exécution trouvée")

    except Exception as e:
        print(f"⚠️  Impossible de récupérer les exécutions: {e}")

if __name__ == "__main__":
    success = trigger_workflow()
    get_workflow_runs()
    sys.exit(0 if success else 1)
