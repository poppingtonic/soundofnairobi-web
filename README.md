# Sound of Nairobi - Funkwhale Modifications
Funkwhale is a SPA built in Django + Vue
We modify it by removing SPA middleware and replacing the Vue frontend with our own backend
change permissions to enable users who are not logged in to view and upload recordings
expose `/uploads`, `/tracks` endpoints

music/models.py
- Add fields for archiving & migrate
- remove ownership

music/tasks.py
- comment out unnecessary metadata we don't need more than model fields for wav files

Original nginx:
funkwhale.conf

New nginx:
soundofnairobi.net.conf           
soundsofnairobitest.wll.world.conf
