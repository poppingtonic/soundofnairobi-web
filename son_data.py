from funkwhale_api.music.tasks import get_track_from_import_metadata
from django.core.files import File
from django.utils import timezone
from django.db import transaction
import os
from funkwhale_api.music import models
import datetime
import csv

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

def bulk_load_recordings(data, path=None):
    for datum in data:
        with transaction.atomic():
            filename = datum["source"].split("://")[1]
            datum['recording_date'] = datetime.datetime.strptime(datum['recording_date'], '%d/%m/%Y %H:%M') if type(datum['recording_date']) is str else datum['recording_date']
            upload = models.Upload(**datum)
            fp = os.path.join(path, filename)
            if os.path.isfile(fp):
                try:
                    with open(fp, 'rb') as recording:
                        upload.audio_file.save(filename, File(recording), save=True)
                        upload.save()
                        process_upload(upload)
                        print(f"processed {filename}")
                except:
                    import pdb; pdb.set_trace()
                    print(f"xxxxxxxxxxx failed at {filename}")
            else:
                print(f"xxxxxxxxxxx {fp} not found") # end function


def read_data_from_csv(csv_path):
    data = []
    with open(csv_path, 'r', newline='') as fp:
        reader = csv.DictReader(fp)
        for d in reader:
            data.append(dict(d))
    return data