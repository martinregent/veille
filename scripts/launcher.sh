#!/bin/bash

# Configuration du chemin absolu du projet
PROJECT_DIR="/Users/martinregent/dev/veille"
# Utilisation du python Homebrew (chemin absolu)
PYTHON_CMD="/opt/homebrew/bin/python3"

# Aller dans le dossier du projet
cd "$PROJECT_DIR" || exit 1

# Vérifier si MkDocs tourne déjà, sinon le lancer
if ! pgrep -f "mkdocs serve" > /dev/null; then
    # Lancer mkdocs via le module python système
    nohup "$PYTHON_CMD" -m mkdocs serve > veille.log 2>&1 &
    
    # Attendre quelques secondes que le serveur démarre
    sleep 2
fi

# Ouvrir l'URL dans le navigateur par défaut
open "http://127.0.0.1:8000"


