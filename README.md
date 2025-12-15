# 📰 Veille Technologique - Architecture Local-First

Un système de veille technologique automatisé, basé sur GitHub Issues comme inbox et Mistral AI pour l'analyse.

## 🎯 Objectif

Centraliser l'ingestion d'articles techniques depuis plusieurs sources (mobile, laptop, email) et générer automatiquement des fiches résumées avec classification.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      INGESTION (Inbox)                       │
│                    GitHub Issues + Labels                    │
│  Mobile → Share to GitHub | Laptop → Browser | Mail → ...   │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRAITEMENT (Local)                         │
│            Python Script + Mistral AI Analysis               │
│  1. Récupère issues with label 'to_process'                 │
│  2. Scrape le contenu de chaque URL                         │
│  3. Appelle Mistral pour résumé + tags + thématique        │
│  4. Génère fichier Markdown structuré                       │
│  5. Ferme issue avec commentaire de succès                  │
└──────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               PUBLICATION & FRONT (Frontend)                │
│              MkDocs + Material Theme + GitHub Pages         │
│            Site statique consultable en ligne               │
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
│   └── process_veille.py           # Script principal de traitement
├── .github/
│   └── workflows/
│       └── publish.yml             # Workflow GitHub Actions
├── mkdocs.yml                      # Configuration MkDocs
├── requirements.txt                # Dépendances Python
├── .env.example                    # Exemple de configuration
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

### 5. Créer le label GitHub

Dans ton repository GitHub :
1. Va sur "Issues" → "Labels"
2. Crée un nouveau label : `to_process` (de couleur jaune par exemple)

## 🚀 Utilisation

### Workflow Quotidien

#### 1️⃣ Ingestion (sur mobile/laptop)

**Sur mobile :**
- Ouvre l'app GitHub officielle
- Va sur ton repo `veille`
- Clique "+"
- Sélectionne "New Issue"
- Mets l'URL de l'article dans la description
- Ajoute le label `to_process`
- Crée l'issue

**Sur laptop :**
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

GitHub Actions se déclenche automatiquement et déploie le site sur GitHub Pages.

#### 4️⃣ Consulter

Visite : `https://martinregent.github.io/veille/`

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

### GitHub Pages ne se met pas à jour

- Vérifie que les GitHub Actions passent (onglet "Actions" du repo)
- Active GitHub Pages dans les settings : `Settings → Pages → Source: GitHub Actions`

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

## 🔐 Sécurité

- **Ne commite jamais ton `.env`** (il est dans `.gitignore`)
- Les tokens GitHub sont limités au repo `veille`
- Les clés API Mistral sont stockées localement seulement

## 📚 Ressources

- [Documentation Mistral AI](https://docs.mistral.ai/)
- [Documentation MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [GitHub API Docs](https://docs.github.com/en/rest)
- [Beautiful Soup Docs](https://www.crummy.com/software/BeautifulSoup/)

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
