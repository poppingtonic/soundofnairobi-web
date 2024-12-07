import os  # For working with files and paths
import datetime  # For handling dates and times
import csv  # For reading CSV files

# Import required Django and Funkwhale functionality
from funkwhale_api.music.tasks import get_track_from_import_metadata
from funkwhale_api.music import models
from django.core.files import File
from django.utils import timezone
from django.db import transaction
from django.db.models import Count

def process_upload(upload):
    """
    Process an uploaded audio file by extracting metadata and creating a track.
    
    Args:
        upload: The Upload model instance to process
    """
    # Get or create empty metadata dictionary
    import_metadata = upload.import_metadata or {}
    
    # Store current status and get audio file
    old_status = upload.import_status
    audio_file = upload.get_audio_file()
    
    # Create track from upload metadata
    additional_data = {}
    final_metadata = upload.__dict__  # Get all upload fields as dict
    track = get_track_from_import_metadata(final_metadata)
    upload.track = track

    # Extract audio metadata if possible
    audio_data = upload.get_audio_data()
    if audio_data:
        upload.duration = audio_data["duration"]
        upload.size = audio_data["size"] 
        upload.bitrate = audio_data["bitrate"]

    # Mark upload as finished and save
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
    """
    Bulk import multiple audio recordings from a data list.
    
    Args:
        data: List of dictionaries containing recording metadata
        path: Base file path where audio files are stored
    """
    for datum in data:
        # Use database transaction to ensure data consistency
        with transaction.atomic():
            # Get filename from source field
            filename = datum["source"].split("://")[1]
            
            # Convert recording date string to datetime if needed
            datum['recording_date'] = (
                datetime.datetime.strptime(datum['recording_date'], '%d/%m/%Y %H:%M') 
                if type(datum['recording_date']) is str 
                else datum['recording_date']
            )

            # Create upload object from metadata
            upload = models.Upload(**datum)
            
            # Build full file path
            fp = os.path.join(path, filename)
            
            # Check if file exists
            if os.path.isfile(fp):
                try:
                    # Open and save audio file
                    with open(fp, 'rb') as recording:
                        upload.audio_file.save(filename, File(recording), save=True)
                        upload.save()
                        process_upload(upload)
                        print(f"processed {filename}")
                except:
                    # If error occurs, start debugger and print message
                    import pdb; pdb.set_trace()
                    print(f"Data Import failed at {filename}")
            else:
                print(f"File {fp} not found")

def read_data_from_csv(csv_path):
    """
    Read data from a CSV file into a list of dictionaries.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of dictionaries containing the CSV data
    """
    data = []
    with open(csv_path, 'r', newline='') as fp:
        reader = csv.DictReader(fp)
        for d in reader:
            data.append(dict(d))
    return data

def deduplicate_uploads():
    """
    Fix duplicate uploads by creating separate tracks for each upload.
    
    This function finds tracks that have multiple uploads associated with them
    and creates new tracks for the duplicate uploads, keeping only one upload
    per track.
    """
    # Use transaction to ensure database consistency
    with transaction.atomic():
        # Find tracks that have multiple uploads
        shared_tracks = models.Track.objects.annotate(
            upload_count=Count('uploads')
        ).filter(upload_count__gt=1)

        for track in shared_tracks:
            # Get all uploads for this track
            uploads = track.uploads.all()
            
            # Keep first upload with original track
            first_upload = uploads[0]

            # Create new tracks for remaining uploads
            for upload in uploads[1:]:
                new_track = models.Track.objects.create(
                    title=track.title,
                    artist=None,
                    album=None,
                    position=track.position,
                    disc_number=track.disc_number,
                    creation_date=track.creation_date
                )
                upload.track = new_track
                upload.save()

        print(f"Deduplication complete. {shared_tracks.count()} tracks were affected.")
