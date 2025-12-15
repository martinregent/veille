# 📰 Veille Technologique

Bienvenue dans ma veille technologique personnelle, basée sur une architecture **Local-First** et **automatisée**.

## 🎯 Concept

Ce système centralise mon ingestion d'articles techniques depuis plusieurs sources (mobile, laptop, email) via un processus simple :

1. **Ingestion** : Créer une Issue GitHub avec l'URL de l'article (label `to_process`)
2. **Traitement** : Un script Python récupère le contenu, l'analyse avec **Mistral AI**
3. **Publication** : Les fiches générées sont indexées ici et déployées automatiquement

## 📁 Structure

- **[Fiches](fiches/)** : Les articles analysés, organisés par date (YYYY/MM)
- **[Tags](tags.md)** : Navigation par thématiques et tags

## 🚀 Workflow Quotidien

### Sur mobile
1. Voir un article sympa → "Share to GitHub"
2. Créer une Issue → Label `to_process` → Done

### Chez moi (le soir)
```bash
python scripts/process_veille.py
```

### Résultat
- Fiches générées automatiquement
- Issues fermées avec commentaires
- Site mis à jour

## 🏗️ Architecture

```
Ingestion (GitHub Issues)
        ↓
   Scraping + Mistral AI
        ↓
   Fiches Markdown
        ↓
   MkDocs + GitHub Pages
```

## 📊 Statistiques

Retrouve les tendances et tags principaux sur la page [Tags](tags.md).

---

*Système Local-First. Pas de base de données externe, pas de serveur complexe.*

*Propulsé par Mistral AI, GitHub, et MkDocs.*
