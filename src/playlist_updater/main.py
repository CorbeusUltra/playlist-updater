# Modules import
import json
import logging
from datetime import datetime, timezone
from pathlib import Path


# Local import
from playlist_update import auth_manager
from playlist_update import youtube_service
from playlist_update.config import PLAYLIST_ID, CHANNEL_ID, DRY_RUN, PLAYLIST_DATA_FILE


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def load_local_state(state_file: Path = PLAYLIST_DATA_FILE) -> dict | None:
    """Charge le fichier JSON ou retourne None si inexistant."""
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_local_state(data: dict, state_file: Path = PLAYLIST_DATA_FILE) -> None:
    """Sauvegarde les données au format JSON standardisé."""
    # Recalcul de la metadata 'latest_video' avant sauvegarde
    if data.get('videos'):
        latest = max(data['videos'], key=lambda x: x['published_at'])
        data['latest_video'] = {
            "video_id": latest['video_id'],
            "published_at": latest['published_at']
        }

    data['extraction_timestamp'] = datetime.now(timezone.utc).isoformat()
    data['total_count'] = len(data.get('videos', []))

    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"[SYSTEM] État local sauvegardé dans {state_file}")

def main(youtube_module=youtube_service, state_file: Path = PLAYLIST_DATA_FILE) -> None:
    # 1. Authentification
    logging.info("--- Initialisation du service YouTube ---")
    youtube = auth_manager.get_authenticated_service()

    # 2. Chargement de l'état local (Base de connaissance)
    local_data = load_local_state(state_file=state_file)

    # Si le fichier n'existe pas, on doit faire une extraction initiale (Bootstrap)
    if not local_data:
        logging.info("[INIT] Pas de données locales. Extraction complète de la playlist actuelle...")
        videos = youtube_module.fetch_all_playlist_items(youtube, PLAYLIST_ID)
        local_data = {
            "playlist_id": PLAYLIST_ID,
            "videos": videos
        }
        save_local_state(local_data, state_file=state_file)

    # 3. Détermination du point de synchronisation
    if 'latest_video' in local_data:
        last_sync_date = local_data['latest_video']['published_at']
    elif local_data.get('videos'):
        latest = max(local_data['videos'], key=lambda x: x['published_at'])
        last_sync_date = latest['published_at']
    else:
        logging.warning("État local présent mais aucune vidéo connue. Abandon.")
        return

    logging.info(f"[INFO] Dernière vidéo connue datant du : {last_sync_date}")

    # 4. Récupération des candidats à l'ajout
    uploads_id = youtube_module.get_channel_uploads_id(youtube, CHANNEL_ID)
    if not uploads_id:
        return

    new_videos = youtube_module.get_new_videos_from_channel(youtube, uploads_id, last_sync_date)

    if not new_videos:
        logging.info("[INFO] Aucune nouvelle vidéo détectée. Le système est à jour.")
        return

    logging.info(f"[DETECT] {len(new_videos)} nouvelles vidéos trouvées !")

    # Inversion pour ajouter les plus anciennes d'abord (respect de l'ordre chronologique)
    new_videos.sort(key=lambda x: x['published_at'])

    # 5. Processus d'ajout (Simulation ou Exécution)
    logging.info("=" * 50)
    mode_str = "[DRY RUN - SIMULATION]" if DRY_RUN else "[PRODUCTION - ÉCRITURE]"
    logging.info(f"{mode_str} Début du traitement")
    logging.info("=" * 50)

    count_success = 0
    for video in new_videos:
        duration = video.get('duration', 'N/A')
        logging.info(f"{video['title']} [{duration}] ({video['published_at']})")

        if DRY_RUN:
            count_success += 1
        else:
            success = youtube_module.add_video_to_playlist(youtube, PLAYLIST_ID, video['video_id'])
            if success:
                logging.info("   -> [SUCCÈS] Ajouté à la playlist.")
                # Mise à jour immédiate de l'état local pour éviter toute perte de données
                local_data['videos'].append(video)
                save_local_state(local_data, state_file=state_file)
                count_success += 1
            else:
                logging.error("   -> [ÉCHEC] Erreur lors de l'ajout.")

    # 6. Finalisation
    logging.info("=" * 50)
    logging.info(f"Terminé. {count_success} vidéos traitées.")

# Préférer lancer depuis `script/run.py`
# if __name__ == "__main__":
#     main()
