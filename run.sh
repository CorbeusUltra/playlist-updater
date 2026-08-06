#!/usr/bin/env bash
# Lance playlist_updater. Fonctionne depuis n'importe quel dossier.
cd "$(dirname "$0")" || exit 1
# Rend le lancement indépendant de l'install editable (survit à un déplacement)
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python3.14 script/run.py "$@"
