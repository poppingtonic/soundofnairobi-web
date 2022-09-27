import mimetypes

import magic
import mutagen
import pydub
import soundfile as sf

from funkwhale_api.common.search import normalize_query, get_query  # noqa

def guess_mimetype_soundofnairobi(f):
    mt, _ = mimetypes.guess_type(f.name)
    if mt:
        return mt

def guess_mimetype(f):
    b = min(1000000, f.size)
    t = magic.from_buffer(f.read(b), mime=True)
    if not t.startswith("audio/"):
        # failure, we try guessing by extension
        mt, _ = mimetypes.guess_type(f.name)
        if mt:
            t = mt
    return t


def compute_status(jobs):
    statuses = jobs.order_by().values_list("status", flat=True).distinct()
    errored = any([status == "errored" for status in statuses])
    if errored:
        return "errored"
    pending = any([status == "pending" for status in statuses])
    if pending:
        return "pending"
    return "finished"


AUDIO_EXTENSIONS_AND_MIMETYPE = [
    ("ogg", "audio/ogg"),
    ("opus", "audio/opus"),
    ("mp3", "audio/mpeg"),
    ("flac", "audio/x-flac"),
    ("flac", "audio/flac"),
    ("wav", "audio/x-wav"),
]

EXTENSION_TO_MIMETYPE = {ext: mt for ext, mt in AUDIO_EXTENSIONS_AND_MIMETYPE}
MIMETYPE_TO_EXTENSION = {mt: ext for ext, mt in AUDIO_EXTENSIONS_AND_MIMETYPE}

SUPPORTED_EXTENSIONS = list(
    sorted(set([ext for ext, _ in AUDIO_EXTENSIONS_AND_MIMETYPE]))
)


def get_ext_from_type(mimetype):
    return MIMETYPE_TO_EXTENSION.get(mimetype)


def get_type_from_ext(extension):
    if extension.startswith("."):
        # we remove leading dot
        extension = extension[1:]
    return EXTENSION_TO_MIMETYPE.get(extension)


def get_audio_file_data(f):
    d = {}
    if guess_mimetype_soundofnairobi(f) == 'audio/x-wav':
        data = sf.SoundFile(f.path)
        d["bitrate"] = data.samplerate
        d["length"] = len(data) / d["bitrate"]
    else:
        data = mutagen.File(f)
        if not data:
            return
        d["bitrate"] = getattr(data.info, "bitrate", 0)
        d["length"] = data.info.length
    return d


def get_actor_from_request(request):
    actor = None
    if hasattr(request, "actor"):
        actor = request.actor
    elif request.user.is_authenticated:
        actor = request.user.actor

    return actor


def transcode_file(input, output, input_format, output_format, **kwargs):
    with input.open("rb"):
        audio = pydub.AudioSegment.from_file(input, format=input_format)
    return transcode_audio(audio, output, output_format, **kwargs)


def transcode_audio(audio, output, output_format, **kwargs):
    with output.open("wb"):
        return audio.export(output, format=output_format, **kwargs)
