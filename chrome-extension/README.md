# 🎯 Extension Chrome - Veille Technologique

Une extension Chrome pour capturer rapidement n'importe quel article et l'ajouter à votre système de veille **sans passer par GitHub**.

## ✨ Fonctionnalités

- ✅ **Capturer en 1 clic** : Ajoute l'article directement à votre veille
- ✅ **Menu contextuel** : Clic droit sur une page ou un lien → "Ajouter à Veille"
- ✅ **Interface clean** : Popup moderne avec thème indigo/violet
- ✅ **Configuration simple** : Stockage sécurisé du token GitHub en local
- ✅ **Notes personnelles** : Ajoute des commentaires à tes captures
- ✅ **Notifications** : Confirmations en temps réel

## 🚀 Installation

### Prérequis

1. **Chrome** (ou tout navigateur basé sur Chromium : Edge, Brave, etc.)
2. **Un GitHub Personal Access Token** avec droits `repo`

### Créer un Personal Access Token

1. Va sur : https://github.com/settings/tokens
2. Clique "Generate new token (classic)"
3. Donne-lui un nom : "Veille Extension"
4. Sélectionne les permissions :
   - ✅ `repo` (accès complet aux repositories)
5. Clique "Generate token"
6. **Copie le token** (⚠️ ne le montrez jamais!)

### Installer l'extension

#### Option 1 : Mode développeur (Recommandé pour tester)

1. Ouvre Chrome
2. Va à `chrome://extensions/`
3. Active le **"Mode de développement"** (en haut à droite)
4. Clique **"Charger l'extension non empaquetée"**
5. Sélectionne le dossier `chrome-extension/`

L'extension s'installe ! 🎉

#### Option 2 : Packaging (Pour distribuer)

```bash
cd chrome-extension
# Zip l'extension
zip -r veille-extension.zip . -x "*.DS_Store"

# Puis tu peux l'envoyer ou la publier
```

## ⚙️ Configuration

### Première utilisation

1. Clique sur l'**icône Veille** (indigo) dans la barre d'outils
2. La popup s'ouvre → tu dois configurer tes identifiants GitHub
3. Remplis les champs :
   - **GitHub Personal Access Token** : Colle ton token
   - **Utilisateur GitHub** : `martinregent` (ou ton username)
   - **Nom du repository** : `veille` (ou le nom de ton repo)
4. Clique **"Sauvegarder la configuration"**

La configuration est stockée **localement** dans `chrome.storage` (sécurisé, jamais envoyé à Chrome).

## 📖 Utilisation

### Méthode 1 : Via le popup

1. Sur n'importe quelle page, clique l'**icône Veille** 📰
2. Le popup affiche :
   - Titre de l'article (auto-détecté)
   - URL (auto-remplie)
   - Champ de note (optionnel)
3. Clique **"✅ Ajouter à la veille"**
4. L'issue GitHub est créée automatiquement avec le label `to_process`
5. Tu vois une confirmation ✅

### Méthode 2 : Via le menu contextuel (Plus rapide!)

#### Capturer le lien
1. **Clic droit** sur un lien n'importe où sur le web
2. Sélectionne **"Ajouter à Veille"** dans le menu
3. 🎉 Article capturé! Notification en bas à droite

#### Capturer la page entière
1. **Clic droit** sur la page (pas sur un lien)
2. Sélectionne **"Ajouter cette page à Veille"**
3. 🎉 Page capturée! Notification en bas à droite

### Flux de travail

**Sur le web (Chrome) :**
```
Voir un article sympa
       ↓
Clic droit → "Ajouter à Veille"
       ↓
🎉 Issue créée automatiquement!
```

**Chez toi (Terminal) :**
```bash
python3 scripts/process_veille.py
```

**Résultat :**
- Fiches générées et publiées
- Extension informée automatiquement 🔔

## 🛠️ Dépannage

### L'extension demande toujours la configuration

**Cause :** Le token n'est pas sauvegardé.

**Solution :**
1. Va à `chrome://extensions/`
2. Trouve "Veille - Capturer des articles"
3. Clique "Détails"
4. Vérifie les permissions
5. Réessaye la configuration

### "Erreur : Token invalide"

**Cause :** Token GitHub expiré ou mal formé.

**Solution :**
1. Génère un nouveau token : https://github.com/settings/tokens
2. Clique sur l'icône Veille
3. Clique "⚙️ Configuration"
4. Mets le nouveau token
5. Sauvegarde

### "Erreur : Repository non trouvé"

**Cause :** Utilisateur GitHub ou nom du repo incorrect.

**Solution :**
1. Vérifie ton username GitHub : https://github.com/settings/profile
2. Vérifie le nom de ton repo : https://github.com/martinregent/veille
3. Clique sur l'icône Veille → "⚙️ Configuration"
4. Corrige les champs
5. Sauvegarde

### L'extension ne capture pas

**Cause :** Peut-être que le site bloque les requêtes cross-origin.

**Solution :**
1. Utilise la **Méthode 2 : Menu contextuel** (plus fiable)
2. Ou utilise le **serveur API local** (voir section ci-dessous)

## 🖥️ Alternative : Serveur API Local

Si tu préfères une approche **sans token stocké dans l'extension**, tu peux utiliser un serveur Python local.

### Lancer le serveur

```bash
python3 scripts/veille_api_server.py
```

Tu verras :
```
╔════════════════════════════════════════════════╗
║         🚀 Veille API Server démarré            ║
╠════════════════════════════════════════════════╣
║ URL:     http://localhost:5888               ║
║ Endpoint: POST http://localhost:5888/api/capture ║
```

### Configurer l'extension pour le serveur

*À implémenter : mode "API Server" dans la configuration*

Pour l'instant, modifie `popup.js` ligne 89 :

```javascript
// À la place d'appeler GitHub directement :
// const issue = await createGitHubIssue(config, url, description);

// Utilise :
// const response = await fetch('http://localhost:5888/api/capture', {...})
```

### Tester le serveur

```bash
curl -X POST http://localhost:5888/api/capture \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com/article",
       "description": "Une note personnelle",
       "tags": ["tag1"]
     }'
```

Réponse :
```json
{
  "status": "success",
  "message": "Issue #42 créée",
  "issue_url": "https://github.com/martinregent/veille/issues/42",
  "issue_number": 42
}
```

## 📝 Architecture

```
Extension Chrome
    ├── popup.html/js
    │   └── Interface de capture
    ├── background.js
    │   └── Menu contextuel + notifications
    ├── manifest.json
    │   └── Configuration de l'extension
    └── icons/
        └── Icônes indigo

        ↓ (Crée des issues via GitHub API)
        ↓

    GitHub Issues
    (label: to_process)

        ↓ (Le script Python traite)
        ↓

    Fiches Markdown + Site MkDocs
```

## 🔐 Sécurité

- **Token stocké localement** dans `chrome.storage` (pas envoyé nulle part)
- **HTTPS uniquement** pour l'API GitHub
- **Permissions minimales** : Nécessite juste `repo` sur GitHub
- **Pas de tracking** : L'extension ne collecte aucune donnée

## 💡 Améliorations futures

- [ ] Support du serveur API local (interface UI)
- [ ] Capture de texte sélectionné (description auto)
- [ ] Détection du titre de l'article (meilleur que `<title>`)
- [ ] Sync avec l'app mobile (PWA)
- [ ] Synchronisation avec Google Keep / Notion
- [ ] Export en PDF avant capture
- [ ] Historique des captures (en local)
- [ ] Raccourcis clavier pour capture rapide

## 📞 Support

Pour les problèmes :
1. Vérifie la console DevTools : `F12` → Onglet "Extensions" → "Errors"
2. Vérifie ton token GitHub
3. Vérifie que le label `to_process` existe sur GitHub

## 🙏 Remerciements

- [Chrome Extensions API](https://developer.chrome.com/docs/extensions/)
- [GitHub REST API](https://docs.github.com/en/rest)
- Thème inspiré par Material Design 3

---

**Prêt ? Lance l'extension et commence à capturer ! 🚀**
