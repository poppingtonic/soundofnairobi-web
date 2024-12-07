# Sound of Nairobi - Funkwhale Modifications
Funkwhale is a SPA built in Django + Vue
We modify it by removing SPA middleware and replacing the Vue frontend with our own backend
change permissions to enable users who are not logged in to view and upload recordings
expose `/uploads`, `/tracks` endpoints

music/models.py
- Add fields for archiving & migrate
Upload fields added:
    + "recording_start_location",
    + "location_latitude",
    + "location_longitude",
    + "recording_route",
    + "recording_description",
    + "recording_name",
    + "recording_thoughts",
    + "recording_special_sounds",
    + "recording_date",
    + "inventory_number"
- remove ownership

music/tasks.py
- comment out unnecessary metadata we don't need more than model fields for wav files


music/serializers.py
UploadSerializer fields added:
    + "recording_start_location",
    + "location_latitude",
    + "location_longitude",
    + "recording_route",
    + "recording_description",
    + "recording_name",
    + "recording_thoughts",
    + "recording_special_sounds",
    + "recording_date"

Original nginx:
funkwhale.conf

New nginx:
soundofnairobi.net.conf           
soundsofnairobitest.wll.world.conf
