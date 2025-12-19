#!/bin/bash

# Configuration
PROJECT_DIR="/Users/martinregent/dev/veille"
PYTHON_CMD="/opt/homebrew/bin/python3"

# Aller dans le dossier
cd "$PROJECT_DIR" || exit 1

echo "🚀 Lancement du processus de veille..."
echo "📂 Dossier : $PROJECT_DIR"
echo "------------------------------------------------"

# Lancer le script python
"$PYTHON_CMD" scripts/process_veille.py

echo "------------------------------------------------"
echo "✅ Terminé."
# Pause pour laisser le temps de lire les logs avant de fermer
read -p "Appuyez sur Entrée pour fermer cette fenêtre..."
