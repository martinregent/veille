# 📰 Veille Technologique - Architecture Local-First

Un système de veille technologique automatisé, basé sur GitHub Issues comme inbox et Mistral AI pour l'analyse.

## 🎯 Objectif

Centraliser l'ingestion d'articles techniques depuis plusieurs sources (mobile, laptop, email) et générer automatiquement des fiches résumées avec classification.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      INGESTION (Inbox)                       │
│                   Extension Chrome + GitHub                  │
│  Articles → Clic droit → "Ajouter à Veille"                 │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
                   GitHub Issues (API)
              (label: to_process)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          TRAITEMENT (GitHub Actions - Auto)                 │
│       Quotidien à 20h UTC ou sur déclenchement manuel       │
│  1. Récupère issues avec label 'to_process'                │
│  2. Scrape le contenu de chaque URL                         │
│  3. Appelle Mistral pour résumé + tags + thématique        │
│  4. Génère fichiers Markdown structurés                     │
│  5. Commit + Push (déclenche le déploiement)               │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│     BUILD (GitHub Actions → MkDocs)                         │
│           pip install + mkdocs build                        │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│     PUBLICATION (Cloudflare Pages - Global CDN)             │
│     Déploiement automatique + Cache global                  │
│     Site statique ultra-rapide disponible 24/7              │
│                                                              │
│         🌐 https://veille.pages.dev                         │
│        (ou domaine custom configuré)                        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Structure du Projet

```
veille/
├── docs/                           # Racine du site MkDocs
│   ├── index.md                    # Page d'accueil
│   ├── tags.md                     # Navigation par tags
│   └── fiches/                     # Fiches générées
│       └── 2025/                   # Organisation par année
│           └── 12/                 # Organisation par mois
│               └── 15-article.md   # Fiches avec timestamp
├── scripts/
│   ├── process_veille.py           # Script principal de traitement
│   └── veille_api_server.py        # Serveur API local (optionnel)
├── chrome-extension/               # 🎯 Extension Chrome pour capturer
│   ├── manifest.json               # Configuration
│   ├── popup.html/js               # Interface
│   ├── background.js               # Service worker
│   └── icons/                      # Icônes
├── .github/
│   └── workflows/
│       ├── deploy-cloudflare.yml   # Déploie sur Cloudflare Pages
│       └── process-and-deploy.yml  # Traite articles + déploie (auto)
├── scripts/
│   └── trigger_deployment.py       # Déclenche manuellement le deploy
├── mkdocs.yml                      # Configuration MkDocs
├── requirements.txt                # Dépendances Python
├── .env.example                    # Exemple de configuration
├── CLOUDFLARE_SETUP.md             # Guide Cloudflare Pages
└── README.md                       # Ce fichier
```

## ⚙️ Configuration

### 1. Cloner le repository

```bash
git clone https://github.com/martinregent/veille.git
cd veille
```

### 2. Créer un fichier `.env`

Copie le fichier exemple et remplis les valeurs :

```bash
cp .env.example .env
```

Édite `.env` et ajoute :

```env
MISTRAL_API_KEY=ta_clé_api_mistral
GITHUB_TOKEN=ton_github_personal_token
GITHUB_USER=martinregent
REPO_NAME=veille
```

### 3. Créer les tokens nécessaires

#### Token Mistral
1. Va sur https://console.mistral.ai/api-keys/
2. Crée une nouvelle clé API
3. Copie-la dans `.env`

#### Token GitHub
1. Va sur https://github.com/settings/tokens
2. Clique "Generate new token (classic)"
3. Sélectionne les droits `repo` (pour lire/écrire les issues)
4. Copie le token dans `.env`

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Installer l'extension Chrome (Optionnel mais recommandé)

L'extension Chrome te permet de capturer les articles en **1 clic**, sans passer par GitHub.

**Installation rapide :**
1. Ouvre `chrome://extensions/`
2. Active le "Mode de développement"
3. Clique "Charger l'extension non empaquetée"
4. Sélectionne le dossier `chrome-extension/`
5. Configure ton token GitHub dans le popup

[Documentation complète de l'extension →](chrome-extension/README.md)

### 6. Créer le label GitHub

Dans ton repository GitHub :
1. Va sur "Issues" → "Labels"
2. Crée un nouveau label : `to_process` (de couleur jaune par exemple)

### 7. Déployer sur Cloudflare Pages (⭐ Recommandé)

Pour un hébergement gratuit, ultra-rapide et global :

**Setup complet :** Voir [CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md)

**Résumé rapide :**
1. Va à https://dash.cloudflare.com/
2. **Pages** → **Connect to Git** → Sélectionne ton repo
3. Build command : `pip install -r requirements.txt && mkdocs build`
4. Output directory : `site`
5. Ajoute les secrets Cloudflare dans GitHub Actions
6. **Deploy!** → Site sur `https://veille.pages.dev`

**Avantages :**
- ✅ Déploiement automatique à chaque push
- ✅ CDN global (Ultra rapide partout)
- ✅ SSL/HTTPS gratuit
- ✅ Domaine custom possible
- ✅ Logs détaillés
- ✅ Gratuit pour toujours

[Guide détaillé →](CLOUDFLARE_SETUP.md)

## 🚀 Utilisation

### Workflow Quotidien

#### 1️⃣ Ingestion (sur mobile/laptop)

1. Installe l'extension depuis `chrome-extension/` (voir [Guide d'installation](chrome-extension/README.md))
2. Sur n'importe quelle page → **Clic droit** → **"Ajouter à Veille"**
3. 🎉 **Mode Local-First :** Si ton serveur local est lancé, la fiche est créée **instantanément** sur ton disque !
4. 🎉 **Fallback GitHub :** Sinon, une issue est créée sur GitHub pour un traitement ultérieur par les Actions.

[En savoir plus sur l'extension →](chrome-extension/README.md)

**Option B : Via GitHub (Mobile ou navigateur sans l'extension)**

Sur mobile :
- Ouvre l'app GitHub officielle
- Va sur ton repo `veille`
- Clique "+"
- Sélectionne "New Issue"
- Mets l'URL de l'article dans la description
- Ajoute le label `to_process`
- Crée l'issue

Sur laptop (sans l'extension) :
- Crée un bookmark vers `https://github.com/martinregent/veille/issues/new`
- Partage l'URL via ce bookmark
- Ajoute le label `to_process`

#### 2️⃣ Traitement (chez toi, le soir)

```bash
python scripts/process_veille.py
```

Le script va :
- ✅ Récupérer toutes les issues avec le label `to_process`
- 📄 Scraper le contenu de chaque URL
- 🤖 Analyser avec Mistral AI
- 📝 Générer les fiches Markdown
- 🔒 Fermer les issues avec commentaires

#### 3️⃣ Publication

```bash
git add .
git commit -m "Update veille"
git push origin main
```

Les workflows GitHub Actions se déclenchent automatiquement :
- ✅ `process-and-deploy.yml` : traite les articles (quotidien ou manuel)
- ✅ `deploy-cloudflare.yml` : déploie sur Cloudflare Pages

#### 4️⃣ Consulter

Visite : **`https://veille.pages.dev`** (ou ton domaine custom)

### Lancer localement

Pour prévisualiser le site avant de pusher :

```bash
mkdocs serve
```

Accède à `http://127.0.0.1:8000`

## 📊 Format des Fiches

Chaque fiche générée a cette structure :

```markdown
---
title: Titre de l'article
tags: [tag1, tag2, tag3]
category: IA & Data
date: 2025-12-15
source: https://example.com/article
issue: "#123"
---

# Titre de l'article

*Source : [lien](url)*

## Résumé

[Résumé généré automatiquement par Mistral - 300-500 mots]

---

**Thématique :** IA & Data

**Tags :** `tag1`, `tag2`, `tag3`

*Généré automatiquement via Mistral AI - Issue #123*
```

## 🌐 Approches d'Ingestion

### Approche 1 : Extension Chrome (Recommandé)

**Avantages :**
- ✅ 1 clic pour capturer
- ✅ Menu contextuel (clic droit)
- ✅ Configuration simple
- ✅ Token stocké localement (sécurisé)
- ✅ Notifications en temps réel

**Installation :**
```bash
1. chrome://extensions/
2. Mode développement ON
3. Charger l'extension → chrome-extension/
4. Configurer le token GitHub
```

[Documentation complète →](chrome-extension/README.md)

### Approche 2 : Serveur API Local

**Avantages :**
- ✅ Approche centralisée
- ✅ Plus de flexibilité
- ✅ Peut servir d'autres clients (mobile app, etc)
- ✅ Token GitHub pas stocké dans l'extension

**Installation :**
```bash
python3 scripts/veille_api_server.py
```

Puis configurer l'extension pour pointer vers `http://localhost:5888/api/capture`

**Endpoint :**
```bash
POST /api/capture
Content-Type: application/json

{
  "url": "https://example.com/article",
  "description": "Optional note",
  "tags": ["tag1", "tag2"]
}
```

## 🛠️ Personalisation

### Modifier les thématiques

Dans le script `scripts/process_veille.py`, ligne 97 :

```python
- La thématique doit être UNE SEULE parmi: [DevOps, IA & Data, Développement, Architecture, Business, Cybersécurité, Infrastructure]
```

### Changer le modèle Mistral

Ligne 116 du script :

```python
model="mistral-large-latest",  # Change ici si tu veux utiliser un autre modèle
```

### Personaliser le site MkDocs

Édite `mkdocs.yml` pour :
- Changer les couleurs
- Modifier le titre du site
- Ajouter des extensions
- Configurer la langue

## 🐛 Dépannage

### Erreur : "MISTRAL_API_KEY non définie"

```bash
# Vérifie que .env existe
ls -la .env

# Vérifie que la clé est définie
cat .env | grep MISTRAL_API_KEY
```

### Erreur : "GITHUB_TOKEN non défini"

Même procédure, vérifie `GITHUB_TOKEN`.

### Le script ne scrape rien

- Vérifie que l'URL est valide et accessible
- Certains sites bloquent les bots simples
- La fiche temporaire dans l'issue te dira si c'est un problème de scraping

### Cloudflare Pages ne déploie pas

**Problème :** Le site ne se met pas à jour après un push

**Solutions :**
1. Vérifie que les workflows GitHub Actions passent : https://github.com/martinregent/veille/actions
2. Vérifie les logs Cloudflare : https://dash.cloudflare.com/ → Pages → veille → Deployments
3. Assure-toi que `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID` sont dans les secrets GitHub
4. Relance manuellement : https://github.com/martinregent/veille/actions → "Process Articles & Deploy" → Run workflow

### Workflow GitHub Actions qui ne s'exécute pas

**Si process-and-deploy.yml ne tourne pas :**

```bash
# Vérifier les secrets
https://github.com/martinregent/veille/settings/secrets/actions

# Secrets requis:
# - MISTRAL_API_KEY
# - GITHUB_TOKEN
# - CLOUDFLARE_API_TOKEN
# - CLOUDFLARE_ACCOUNT_ID
```

**Déclencher manuellement :**
```bash
python3 scripts/trigger_deployment.py
# Ou via UI: Actions → Process Articles & Deploy → Run workflow
```

## 📝 Exemples

### Créer une issue pour un article

**Via GitHub Web :**
1. `https://github.com/martinregent/veille/issues/new`
2. Title: (laisse vide ou mets un titre temporaire)
3. Description: `https://example.com/interesting-article`
4. Labels: `to_process`
5. "Create issue"

**Via mobile app :**
- Share → GitHub → veille repo → Create Issue

### Lancer le traitement

```bash
cd /Users/martinregent/dev/veille
python scripts/process_veille.py
```

Résultat attendu :
```
🚀 Démarrage du traitement de la veille...

🔍 2 lien(s) à traiter...

[1/2] Issue #1: https://example.com/article-1
   ✅ Fiche créée: docs/fiches/2025/12/15-article-1.md
   🔒 Issue #1 fermée

[2/2] Issue #2: https://example.com/article-2
   ✅ Fiche créée: docs/fiches/2025/12/15-article-2.md
   🔒 Issue #2 fermée

==================================================
✅ Succès: 2
❌ Erreurs: 0
==================================================
```

### Déclencher manuellement le déploiement

Si tu veux forcer l'exécution du workflow sans attendre l'heure prévue :

```bash
python3 scripts/trigger_deployment.py
```

Affichera :
```
🚀 Déclenchement du workflow 'process-and-deploy.yml'...
✅ Workflow déclenché avec succès!

📊 Suivi: https://github.com/martinregent/veille/actions
🌐 Site: https://veille.pages.dev
```

Ou depuis GitHub UI : https://github.com/martinregent/veille/actions → "Process Articles & Deploy" → "Run workflow"

## 🔐 Sécurité

- **Ne commite jamais ton `.env`** (il est dans `.gitignore`)
- **Secrets GitHub** : Stockés de manière chiffrée et sécurisée
- **Tokens limités** : GitHub token limité au droit `repo`
- **Clés API Mistral** : Utilisées uniquement par GitHub Actions en environnement isolé
- **Token Cloudflare** : Limité à `Pages - Edit` uniquement

## 📊 Monitoring

**Suivi des déploiements :**
- GitHub Actions : https://github.com/martinregent/veille/actions
- Cloudflare Pages : https://dash.cloudflare.com/ → Pages → veille
- Uptime : https://veille.pages.dev (vérifie que le site est accessible)

**Logs disponibles :**
- GitHub Actions : Détails de chaque workflow
- Cloudflare : Logs de build + déploiement
- Analytics : Cloudflare Pages Analytics (traffic, performance)

## 📚 Ressources

- [Documentation Cloudflare Pages](https://developers.cloudflare.com/pages/)
- [Documentation Mistral AI](https://docs.mistral.ai/)
- [Documentation MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [GitHub API Docs](https://docs.github.com/en/rest)
- [Beautiful Soup Docs](https://www.crummy.com/software/BeautifulSoup/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🎨 Améliorations Futures

- [ ] Webhooks GitHub pour trigger auto du script
- [ ] Support du scraping pour sites complexes (Selenium)
- [ ] Export vers formats supplémentaires (PDF, EPUB)
- [ ] Dashboard de statistiques
- [ ] Intégration avec des agrégateurs (RSS, etc)
- [ ] Support multi-langues dans les résumés

## 📞 Support

Pour les problèmes :
1. Vérifie les logs du script
2. Vérifie les GitHub Actions logs
3. Crée une issue dans ce repo

---

**Maintenant, c'est prêt ! À toi de jouer ! 🚀**
