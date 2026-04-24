# Modules import
import json
from datetime import datetime, timezone


# Local import
from playlist_update import auth_manager
from playlist_update import youtube_service
from playlist_update.config import PLAYLIST_ID, CHANNEL_ID, DRY_RUN, PLAYLIST_DATA_FILE





def load_local_state(state_file=PLAYLIST_DATA_FILE):
    """Charge le fichier JSON ou retourne None si inexistant."""
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_local_state(data, state_file=PLAYLIST_DATA_FILE):
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

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[SYSTEM] État local sauvegardé dans {state_file}")

def main(youtube_module=youtube_service, state_file=PLAYLIST_DATA_FILE):
    # 1. Authentification
    print("--- Initialisation du service YouTube ---")
    youtube = auth_manager.get_authenticated_service()

    # 2. Chargement de l'état local (Base de connaissance)
    local_data = load_local_state(state_file=state_file)

    # Si le fichier n'existe pas, on doit faire une extraction initiale (Bootstrap)
    if not local_data:
        print("[INIT] Pas de données locales. Extraction complète de la playlist actuelle...")
        videos = youtube_module.fetch_all_playlist_items(youtube, PLAYLIST_ID)
        local_data = {
            "playlist_id": PLAYLIST_ID,
            "videos": videos
        }
        save_local_state(local_data, state_file=state_file)
    
    # 3. Détermination du point de synchronisation
    if 'latest_video' in local_data:
        last_sync_date = local_data['latest_video']['published_at']
    else:
        # Fallback si le JSON est ancien format
        latest = max(local_data['videos'], key=lambda x: x['published_at'])
        last_sync_date = latest['published_at']

    print(f"[INFO] Dernière vidéo connue datant du : {last_sync_date}")

    # 4. Récupération des candidats à l'ajout
    uploads_id = youtube_module.get_channel_uploads_id(youtube, CHANNEL_ID)
    if not uploads_id:
        return

    new_videos = youtube_module.get_new_videos_from_channel(youtube, uploads_id, last_sync_date)

    if not new_videos:
        print("[INFO] Aucune nouvelle vidéo détectée. Le système est à jour.")
        return

    print(f"\n[DETECT] {len(new_videos)} nouvelles vidéos trouvées !")
    
    # Inversion pour ajouter les plus anciennes d'abord (respect de l'ordre chronologique)
    new_videos.sort(key=lambda x: x['published_at'])

    # 5. Processus d'ajout (Simulation ou Exécution)
    print("\n" + "="*50)
    mode_str = "[DRY RUN - SIMULATION]" if DRY_RUN else "[PRODUCTION - ÉCRITURE]"
    print(f"{mode_str} Début du traitement")
    print("="*50)

    count_success = 0
    for video in new_videos:
        duration = video.get('duration', 'N/A')
        print(f"{video['title']} [{duration}] ({video['published_at']})")
        
        if DRY_RUN:
            # print(f"   -> [SIMULATION] Ajout à la playlist {PLAYLIST_ID}")
            count_success += 1
        else:
            success = youtube_module.add_video_to_playlist(youtube, PLAYLIST_ID, video['video_id'])
            if success:
                print(f"   -> [SUCCÈS] Ajouté à la playlist.")
                # Mise à jour immédiate de l'état local pour éviter toute perte de données
                local_data['videos'].append(video)
                save_local_state(local_data, state_file=state_file)
                count_success += 1
            else:
                print(f"   -> [ÉCHEC] Erreur lors de l'ajout.")

    # 6. Finalisation
    
    print("\n" + "="*50)
    print(f"Terminé. {count_success} vidéos traitées.")

# Préférer lancer depuis `script/run.py`
# if __name__ == "__main__":
#     main()
