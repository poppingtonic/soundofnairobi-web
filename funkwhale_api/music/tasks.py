import collections
import datetime
import logging
import os

from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q
from django.dispatch import receiver

from musicbrainzngs import ResponseError
from requests.exceptions import RequestException

from funkwhale_api.common import channels, preferences
from funkwhale_api.federation import routes
from funkwhale_api.federation import library as lb
from funkwhale_api.taskapp import celery

from . import licenses
from . import models
from . import metadata
from . import signals
from . import serializers

logger = logging.getLogger(__name__)


def update_album_cover(
    album, source=None, cover_data=None, musicbrainz=True, replace=False
):
    if album.cover and not replace:
        return
    if cover_data:
        return album.get_image(data=cover_data)

    if source and source.startswith("file://"):
        # let's look for a cover in the same directory
        path = os.path.dirname(source.replace("file://", "", 1))
        logger.info("[Album %s] scanning covers from %s", album.pk, path)
        cover = get_cover_from_fs(path)
        if cover:
            return album.get_image(data=cover)
    if musicbrainz and album.mbid:
        try:
            logger.info(
                "[Album %s] Fetching cover from musicbrainz release %s",
                album.pk,
                str(album.mbid),
            )
            return album.get_image()
        except ResponseError as exc:
            logger.warning(
                "[Album %s] cannot fetch cover from musicbrainz: %s", album.pk, str(exc)
            )


IMAGE_TYPES = [("jpg", "image/jpeg"), ("png", "image/png")]


def get_cover_from_fs(dir_path):
    if os.path.exists(dir_path):
        for e, m in IMAGE_TYPES:
            cover_path = os.path.join(dir_path, "cover.{}".format(e))
            if not os.path.exists(cover_path):
                logger.debug("Cover %s does not exists", cover_path)
                continue
            with open(cover_path, "rb") as c:
                logger.info("Found cover at %s", cover_path)
                return {"mimetype": m, "content": c.read()}


@celery.app.task(name="music.start_library_scan")
@celery.require_instance(
    models.LibraryScan.objects.select_related().filter(status="pending"), "library_scan"
)
def start_library_scan(library_scan):
    try:
        data = lb.get_library_data(library_scan.library.fid, actor=library_scan.actor)
    except Exception:
        library_scan.status = "errored"
        library_scan.save(update_fields=["status", "modification_date"])
        raise
    library_scan.modification_date = timezone.now()
    library_scan.status = "scanning"
    library_scan.total_files = data["totalItems"]
    library_scan.save(update_fields=["status", "modification_date", "total_files"])
    scan_library_page.delay(library_scan_id=library_scan.pk, page_url=data["first"])


@celery.app.task(
    name="music.scan_library_page",
    retry_backoff=60,
    max_retries=5,
    autoretry_for=[RequestException],
)
@celery.require_instance(
    models.LibraryScan.objects.select_related().filter(status="scanning"),
    "library_scan",
)
def scan_library_page(library_scan, page_url):
    data = lb.get_library_page(library_scan.library, page_url, library_scan.actor)
    uploads = []

    for item_serializer in data["items"]:
        upload = item_serializer.save(library=library_scan.library)
        uploads.append(upload)

    library_scan.processed_files = F("processed_files") + len(uploads)
    library_scan.modification_date = timezone.now()
    update_fields = ["modification_date", "processed_files"]

    next_page = data.get("next")
    fetch_next = next_page and next_page != page_url

    if not fetch_next:
        update_fields.append("status")
        library_scan.status = "finished"
    library_scan.save(update_fields=update_fields)

    if fetch_next:
        scan_library_page.delay(library_scan_id=library_scan.pk, page_url=next_page)


def getter(data, *keys, default=None):
    if not data:
        return default
    v = data
    for k in keys:
        try:
            v = v[k]
        except KeyError:
            return default

    return v


class UploadImportError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail_import(upload, error_code, detail=None, **fields):
    old_status = upload.import_status
    upload.import_status = "errored"
    upload.import_details = {"error_code": error_code, "detail": detail}
    upload.import_details.update(fields)
    upload.import_date = timezone.now()
    upload.save(update_fields=["import_details", "import_status", "import_date"])

    broadcast = getter(
        upload.import_metadata, "funkwhale", "config", "broadcast", default=True
    )
    if broadcast:
        signals.upload_import_status_updated.send(
            old_status=old_status,
            new_status=upload.import_status,
            upload=upload,
            sender=None,
        )


@celery.app.task(name="music.process_upload")
@celery.require_instance(
    models.Upload.objects.filter(import_status="pending"),
    "upload",
)
def process_upload(upload):
    import_metadata = upload.import_metadata or {}
    old_status = upload.import_status
    audio_file = upload.get_audio_file()
    additional_data = {}

    final_metadata = upload.__dict__
    track = get_track_from_import_metadata(
        final_metadata
    )
    upload.track = track

    # all is good, let's finalize the import
    audio_data = upload.get_audio_data()
    if audio_data:
        upload.duration = audio_data["duration"]
        upload.size = audio_data["size"]
        upload.bitrate = audio_data["bitrate"]
    upload.import_status = "finished"
    upload.import_date = timezone.now()
    upload.save(
        update_fields=[
            "track",
            "import_status",
            "import_date",
            "size",
            "duration",
            "bitrate",
        ]
    )


def federation_audio_track_to_metadata(payload, references):
    """
    Given a valid payload as returned by federation.serializers.TrackSerializer.validated_data,
    returns a correct metadata payload for use with get_track_from_import_metadata.
    """
    new_data = {
        "title": payload["name"],
        "position": payload.get("position") or 1,
        "disc_number": payload.get("disc"),
        "license": payload.get("license"),
        "copyright": payload.get("copyright"),
        "attributed_to": references.get(payload.get("attributedTo")),
        "mbid": str(payload.get("musicbrainzId"))
        if payload.get("musicbrainzId")
        else None,
        "album": {
            "title": payload["album"]["name"],
            "fdate": payload["album"]["published"],
            "fid": payload["album"]["id"],
            "attributed_to": references.get(payload["album"].get("attributedTo")),
            "mbid": str(payload["album"]["musicbrainzId"])
            if payload["album"].get("musicbrainzId")
            else None,
            "release_date": payload["album"].get("released"),
            "artists": [
                {
                    "fid": a["id"],
                    "name": a["name"],
                    "fdate": a["published"],
                    "attributed_to": references.get(a.get("attributedTo")),
                    "mbid": str(a["musicbrainzId"]) if a.get("musicbrainzId") else None,
                }
                for a in payload["album"]["artists"]
            ],
        },
        "artists": [
            {
                "fid": a["id"],
                "name": a["name"],
                "fdate": a["published"],
                "attributed_to": references.get(a.get("attributedTo")),
                "mbid": str(a["musicbrainzId"]) if a.get("musicbrainzId") else None,
            }
            for a in payload["artists"]
        ],
        # federation
        "fid": payload["id"],
        "fdate": payload["published"],
    }
    cover = payload["album"].get("cover")
    if cover:
        new_data["cover_data"] = {"mimetype": cover["mediaType"], "url": cover["href"]}
    return new_data


def get_owned_duplicates(upload, track):
    """
    Ensure we skip duplicate tracks to avoid wasting user/instance storage
    """
    owned_libraries = upload.library.actor.libraries.all()
    return (
        models.Upload.objects.filter(
            track__isnull=False, library__in=owned_libraries, track=track
        )
        .exclude(pk=upload.pk)
        .values_list("uuid", flat=True)
    )


def get_best_candidate_or_create(model, query, defaults, sort_fields):
    """
    Like queryset.get_or_create() but does not crash if multiple objects
    are returned on the get() call
    """
    candidates = model.objects.filter(query)
    if candidates:

        return sort_candidates(candidates, sort_fields)[0], False

    return model.objects.create(**defaults), True


def sort_candidates(candidates, important_fields):
    """
    Given a list of objects and a list of fields,
    will return a sorted list of those objects by score.

    Score is higher for objects that have a non-empty attribute
    that is also present in important fields::

        artist1 = Artist(mbid=None, fid=None)
        artist2 = Artist(mbid="something", fid=None)

        # artist2 has a mbid, so is sorted first
        assert sort_candidates([artist1, artist2], ['mbid'])[0] == artist2

    Only supports string fields.
    """

    # map each fields to its score, giving a higher score to first fields
    fields_scores = {f: i + 1 for i, f in enumerate(sorted(important_fields))}
    candidates_with_scores = []
    for candidate in candidates:
        current_score = 0
        for field, score in fields_scores.items():
            v = getattr(candidate, field, "")
            if v:
                current_score += score

        candidates_with_scores.append((candidate, current_score))

    return [c for c, s in reversed(sorted(candidates_with_scores, key=lambda v: v[1]))]


@transaction.atomic
def get_track_from_import_metadata(data, update_cover=False, attributed_to=None):
    track = _get_track(data, attributed_to=attributed_to)
    return track


def _get_track(data, attributed_to=None):
    # get / create track
    track_title = data["recording_name"]
    position = 1
    query = Q(title__iexact=track_title)
    defaults = {
        "title": track_title,
        "album": None,
        "mbid": None,
        "artist": None,
        "position": position,
        "disc_number": None,
        "fid": None,
        "from_activity_id": None,
        "attributed_to": None,
        "license": licenses.match(data.get("license"), data.get("copyright")),
        "copyright": data.get("copyright"),
    }
    if data.get("recording_date"):
        defaults["creation_date"] = data.get("recording_date")

    track, created = get_best_candidate_or_create(
        models.Track, query, defaults=defaults, sort_fields=["mbid", "fid"]
    )
    return track

@receiver(signals.upload_import_status_updated)
def broadcast_import_status_update_to_owner(old_status, new_status, upload, **kwargs):
    user = upload.library.actor.get_user()
    if not user:
        return

    group = "user.{}.imports".format(user.pk)
    channels.group_send(
        group,
        {
            "type": "event.send",
            "text": "",
            "data": {
                "type": "import.status_updated",
                "upload": serializers.UploadForOwnerSerializer(upload).data,
                "old_status": old_status,
                "new_status": new_status,
            },
        },
    )


@celery.app.task(name="music.clean_transcoding_cache")
def clean_transcoding_cache():
    delay = preferences.get("music__transcoding_cache_duration")
    if delay < 1:
        return  # cache clearing disabled
    limit = timezone.now() - datetime.timedelta(minutes=delay)
    candidates = (
        models.UploadVersion.objects.filter(
            (Q(accessed_date__lt=limit) | Q(accessed_date=None))
        )
        .only("audio_file", "id")
        .order_by("id")
    )
    return candidates.delete()


def get_prunable_tracks(
    exclude_favorites=True, exclude_playlists=True, exclude_listenings=True
):
    """
    Returns a list of tracks with no associated uploads,
    excluding the one that were listened/favorited/included in playlists.
    """

    queryset = models.Track.objects.all()
    queryset = queryset.filter(uploads__isnull=True)
    if exclude_favorites:
        queryset = queryset.filter(track_favorites__isnull=True)
    if exclude_playlists:
        queryset = queryset.filter(playlist_tracks__isnull=True)
    if exclude_listenings:
        queryset = queryset.filter(listenings__isnull=True)

    return queryset


def get_prunable_albums():
    return models.Album.objects.filter(tracks__isnull=True)


def get_prunable_artists():
    return models.Artist.objects.filter(tracks__isnull=True, albums__isnull=True)


def update_library_entity(obj, data):
    """
    Given an obj and some updated fields, will persist the changes on the obj
    and also check if the entity need to be aliased with existing objs (i.e
    if a mbid was added on the obj, and match another entity with the same mbid)
    """
    for key, value in data.items():
        setattr(obj, key, value)

    # Todo: handle integrity error on unique fields (such as MBID)
    obj.save(update_fields=list(data.keys()))

    return obj
