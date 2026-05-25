import logging
import re
from datetime import datetime

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from playlist_updater.config import SHORTS_MIN_SECONDS

logger = logging.getLogger(__name__)


def parse_duration(duration_iso: str | None) -> tuple[str, int]:
    """
    Convertit une durée ISO 8601 (ex: PT4M13S) en format lisible (4:13).
    Retourne un tuple: (format_lisible, secondes_totales)
    """
    if not duration_iso:
        return ("0:00", 0)

    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    if not match:
        return ("0:00", 0)

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total_seconds = hours * 3600 + minutes * 60 + seconds

    if hours > 0:
        formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        formatted = f"{minutes}:{seconds:02d}"

    return (formatted, total_seconds)

def fetch_all_playlist_items(youtube: Resource, playlist_id: str) -> list[dict]:
    """
    Récupère exhaustivement les métadonnées d'une playlist.
    Retourne une liste de dictionnaires.
    """
    videos: list[dict] = []
    next_page_token = None

    try:
        while True:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            # Récupération des IDs pour obtenir les durées
            video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]

            # Récupération des durées via l'API videos
            durations: dict[str, str] = {}
            if video_ids:
                videos_response = youtube.videos().list(
                    part="contentDetails",
                    id=",".join(video_ids)
                ).execute()

                for video_item in videos_response.get('items', []):
                    vid_id = video_item['id']
                    duration_iso = video_item['contentDetails'].get('duration', 'PT0S')
                    formatted, _ = parse_duration(duration_iso)
                    durations[vid_id] = formatted

            for item in response.get('items', []):
                vid_id = item['contentDetails']['videoId']
                videos.append({
                    "video_id": vid_id,
                    "title": item['snippet']['title'],
                    "published_at": item['contentDetails'].get('videoPublishedAt'),
                    "duration": durations.get(vid_id, "0:00")
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return videos
    except HttpError as e:
        logger.error(f"[API ERROR] Échec de récupération de la playlist : {e}")
        return []

def get_channel_uploads_id(youtube: Resource, channel_id: str) -> str | None:
    """
    Récupère l'ID de la playlist système 'uploads' d'une chaîne donnée.
    C'est beaucoup moins coûteux (1 unité) que d'utiliser search().
    """
    try:
        response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        if not response['items']:
            raise ValueError(f"Aucune chaîne trouvée avec l'ID {channel_id}")

        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except HttpError as e:
        logger.error(f"[API ERROR] Impossible de récupérer les détails de la chaîne : {e}")
        return None

def get_new_videos_from_channel(youtube: Resource, uploads_playlist_id: str, last_sync_date_iso: str) -> list[dict]:
    """
    Récupère les vidéos de la chaîne publiées strictement APRÈS last_sync_date_iso.
    Filtre: Ne garde que les vidéos dont la durée est > SHORTS_MIN_SECONDS secondes.
    Optimisation : s'arrête dès qu'une vidéo plus ancienne est rencontrée.
    """
    new_videos: list[dict] = []
    next_page_token = None

    # Conversion de la date de référence pour comparaison
    # On gère le 'Z' final si présent pour compatibilité fromisoformat
    ref_date = datetime.fromisoformat(last_sync_date_iso.replace('Z', '+00:00'))

    logger.info(f"[SYNC] Recherche de vidéos publiées après {ref_date}...")

    try:
        while True:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            items = response.get('items', [])
            if not items:
                break

            # Récupération des IDs pour obtenir les durées
            video_ids = [item['contentDetails']['videoId'] for item in items]

            # Récupération des durées via l'API videos
            durations: dict[str, tuple[str, int]] = {}  # {video_id: (formatted, seconds)}
            if video_ids:
                videos_response = youtube.videos().list(
                    part="contentDetails",
                    id=",".join(video_ids)
                ).execute()

                for video_item in videos_response.get('items', []):
                    vid_id = video_item['id']
                    duration_iso = video_item['contentDetails'].get('duration', 'PT0S')
                    durations[vid_id] = parse_duration(duration_iso)

            for item in items:
                vid_date_str = item['contentDetails']['videoPublishedAt']
                vid_date = datetime.fromisoformat(vid_date_str.replace('Z', '+00:00'))
                vid_id = item['contentDetails']['videoId']

                if vid_date > ref_date:
                    # Récupération de la durée (format lisible, secondes totales)
                    formatted_duration, total_seconds = durations.get(vid_id, ("0:00", 0))

                    # Filtre: garder uniquement les vidéos > SHORTS_MIN_SECONDS secondes (exclut les Shorts)
                    if total_seconds > SHORTS_MIN_SECONDS:
                        new_videos.append({
                            "video_id": vid_id,
                            "title": item['snippet']['title'],
                            "published_at": vid_date_str,
                            "duration": formatted_duration
                        })
                else:
                    # Hypothèse forte : la playlist uploads est triée par date décroissante.
                    # On peut donc arrêter la recherche ici pour économiser le quota.
                    return new_videos

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return new_videos
    except HttpError as e:
        logger.error(f"[API ERROR] Erreur lors du scan des nouvelles vidéos : {e}")
        return []

def add_video_to_playlist(youtube: Resource, playlist_id: str, video_id: str) -> bool:
    """
    Ajoute une vidéo spécifique à la playlist cible.
    Coût : 50 unités par appel.
    Retourne True si ajouté avec succès ou si déjà présent.
    """
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body=body
        ).execute()
        return True
    except HttpError as e:
        # Si la vidéo existe déjà (code 409 ou message spécifique), on considère ça comme un succès
        error_details = str(e)
        if "videoAlreadyInPlaylist" in error_details or e.resp.status == 409:
            logger.info(f"[INFO] La vidéo {video_id} est déjà dans la playlist.")
            return True
        logger.error(f"[API ERROR] Échec de l'ajout de la vidéo {video_id} : {e}")
        return False
