# 🌐 Configuration Cloudflare Pages

Guide complet pour déployer ton site de veille sur **Cloudflare Pages** avec déploiement automatique.

## 📋 Prérequis

- Un compte Cloudflare (gratuit)
- Ton repo GitHub `martinregent/veille`
- Un Personal Access Token GitHub (déjà créé)

## 🚀 Setup Cloudflare Pages

### Étape 1 : Créer un compte Cloudflare

1. Va à https://dash.cloudflare.com/
2. **Sign Up** (gratuit)
3. Crée un compte avec email + password
4. Confirme ton email

### Étape 2 : Connecter GitHub à Cloudflare Pages

1. Va à https://dash.cloudflare.com/
2. Clique **Pages** (menu de gauche)
3. Clique **"Create a project"**
4. Sélectionne **"Connect to Git"**
5. **Choose GitHub** → Autorise Cloudflare sur ton compte GitHub

### Étape 3 : Configurer le déploiement

1. Sélectionne le repo : `martinregent/veille`
2. Branche : `main`
3. **Build settings :**
   - **Framework preset** : `None` (on va make manuel)
   - **Build command** : `pip install -r requirements.txt && mkdocs build`
   - **Build output directory** : `site`
4. Clique **"Save and Deploy"**

Cloudflare va :
- ✅ Cloner ton repo
- ✅ Installer les dépendances
- ✅ Builder MkDocs
- ✅ Déployer sur `https://veille.pages.dev`

### Étape 4 : Configurer les secrets GitHub Actions

Pour que le workflow GitHub Actions puisse déployer sur Cloudflare, il faut des tokens.

**Obtenir les infos Cloudflare :**

1. Va à https://dash.cloudflare.com/profile/api-tokens
2. Clique **"Create Token"** → **"Custom Token"**
3. Configure :
   - **Permissions** :
     - `Account.Cloudflare Pages` → `Edit`
     - `Zone.Zone` → `Read` (si domaine custom)
   - **Account Resources** : Ta compte
   - **Zone Resources** : Tous les domaines
4. Clique **"Create Token"**
5. **Copie le token**

**Obtenir l'Account ID :**

1. Va à https://dash.cloudflare.com/
2. Regarde en bas à droite : il y a un "Account ID"
3. Ou va à n'importe quelle page → Overview → en bas à droite

### Étape 5 : Ajouter les secrets GitHub

1. Va à ton repo GitHub : `https://github.com/martinregent/veille`
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** :
   - **Name** : `CLOUDFLARE_API_TOKEN`
   - **Value** : (colle le token créé ci-dessus)
4. **New repository secret** :
   - **Name** : `CLOUDFLARE_ACCOUNT_ID`
   - **Value** : (colle ton Account ID)
5. Ajoute aussi si pas déjà présent :
   - **Name** : `MISTRAL_API_KEY`
   - **Value** : ta clé Mistral

## 🔄 Workflows automatiques

Deux workflows sont maintenant configurés :

### Workflow 1 : `deploy-cloudflare.yml`

**Se déclenche quand :**
- Push sur `main` qui modifie `docs/`, `mkdocs.yml`, ou `requirements.txt`
- Déclenchement manuel

**Fait :**
- Build MkDocs
- Déploie directement sur Cloudflare Pages

### Workflow 2 : `process-and-deploy.yml`

**Se déclenche quand :**
- **Quotidien** à 20h UTC (configurable)
- Push d'une issue (GitHub Issues)
- Déclenchement manuel

**Fait :**
- Lance `python scripts/process_veille.py`
- Traite les articles avec le label `to_process`
- Crée des fiches Markdown
- Commit et push (déclenche le déploiement)

## 📊 Flux de déploiement complet

```

Utilisateur
   ↓
Clic droit → "Ajouter à Veille"
   ↓
Extension Chrome crée une issue GitHub
   ↓
Issues GitHub (label: to_process)
   ↓
GitHub Actions : process-and-deploy.yml
   ↓
python scripts/process_veille.py
   ↓
Génère fiches Markdown dans docs/fiches/
   ↓
Git commit + push
   ↓
GitHub Actions : deploy-cloudflare.yml
   ↓
Build MkDocs
   ↓
Déploie sur Cloudflare Pages
   ↓
🌐 https://veille.pages.dev ✅
```

## 🎮 Déclencher manuellement

### Option 1 : Via GitHub UI

1. Va à https://github.com/martinregent/veille/actions
2. Sélectionne **"Process Articles & Deploy"**
3. Clique **"Run workflow"** → **"Run workflow"**

### Option 2 : Via le script Python

```bash
# Vérifier que .env est configuré
python3 scripts/trigger_deployment.py
```

Affiche :
```
🚀 Déclenchement du workflow 'process-and-deploy.yml'...
✅ Workflow déclenché avec succès!

📊 Suivi: https://github.com/martinregent/veille/actions
🌐 Site: https://veille.pages.dev
```

### Option 3 : Via curl (API GitHub)

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/martinregent/veille/actions/workflows/process-and-deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

## 📍 Domaine custom (optionnel)

Si tu as un domaine custom :

1. Va à https://dash.cloudflare.com/ → Pages → veille
2. **Settings** → **Custom domains**
3. Ajoute ton domaine : `veille.example.com`
4. Configure le DNS chez ton registraire

Cloudflare te donnera les CNAME à ajouter.

## 🔍 Monitoring & Dépannage

### Voir l'état des déploiements

**GitHub Actions :**
```
https://github.com/martinregent/veille/actions
```

**Cloudflare Pages :**
```
https://dash.cloudflare.com/ → Pages → veille
```

### Logs d'exécution

1. Va à https://github.com/martinregent/veille/actions
2. Clique sur le workflow qui t'intéresse
3. Clique sur l'exécution
4. Voir les logs détaillés

### Logs Cloudflare

1. Va à https://dash.cloudflare.com/
2. Pages → veille → Deployments
3. Clique sur un déploiement → Logs

### Problèmes courants

**❌ Workflow n'exécute pas le script Python**

Vérifier que `MISTRAL_API_KEY` et `GITHUB_TOKEN` sont dans les secrets.

```bash
# Localement, test :
python3 scripts/process_veille.py
```

**❌ Cloudflare Pages ne se déploie pas**

Vérifier :
- `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID` dans secrets GitHub
- Le build command est correct : `pip install -r requirements.txt && mkdocs build`
- L'output directory est `site`

**❌ Les fiches ne sont pas traitées**

Vérifier que le label `to_process` existe sur GitHub :
```
https://github.com/martinregent/veille/labels
```

## 📈 Optimisations avancées

### Changer l'heure du traitement quotidien

Dans `.github/workflows/process-and-deploy.yml`, ligne 7 :

```yaml
schedule:
  - cron: '0 20 * * *'  # 20h UTC
  # Exemples:
  # '0 9 * * *'   → 9h UTC
  # '0 0 * * 0'   → Dimanche 00h UTC
  # '30 14 * * 1' → Lundi 14h30 UTC
```

[Référence cron](https://crontab.guru/)

### Ignorer certains fichiers du déploiement

Dans `mkdocs.yml` :

```yaml
docs_dir: docs
site_dir: site
```

### Activer un CDN custom

Voir la doc Cloudflare Pages :
https://developers.cloudflare.com/pages/configuration/

## 📝 Checklist finale

- [ ] Compte Cloudflare créé
- [ ] Repo connecté à Cloudflare Pages
- [ ] Build settings configurés
- [ ] `CLOUDFLARE_API_TOKEN` ajouté à secrets GitHub
- [ ] `CLOUDFLARE_ACCOUNT_ID` ajouté à secrets GitHub
- [ ] `MISTRAL_API_KEY` présent dans secrets GitHub
- [ ] Label `to_process` créé sur GitHub
- [ ] Extension Chrome installée
- [ ] Premier article testé
- [ ] Déploiement automatique vérifié sur https://veille.pages.dev

---

**C'est prêt!** Ton site est maintenant sur Cloudflare Pages avec déploiement automatique! 🚀

Besoin d'aide? Consulte les logs GitHub Actions ou Cloudflare Pages.
