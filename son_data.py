from funkwhale_api.music.tasks import get_track_from_import_metadata
from django.core.files import File
from django.utils import timezone
from django.db import transaction
import os
from funkwhale_api.music import models
import csv

# test:coord=1°14\'32.9\"S
def clean_coordinates(coord="1°14\'32.9\"S"):
    pass

data = [
    {
        "recording_start_location": "Landhies Road",
        "location_latitude": -1.2871685,
        "location_longitude": 36.83652099999995,
        "recording_route": "Bike Then walking Landhies Road end to end, Jua Kali Place – Kamkunji Grounds",
        "recording_description": "Binaural microphone",
        "recording_name": "Alacoque_ZOOM0034_EQ",
        "recording_special_sounds": "Tuk Tuk sounds moving and stationary, Tuk tuk hooting, a person whistling, a truck, People speaking different languages,(swahili, Kikuyu and hoped to hear some Dholuo), metal workers, hum of a truck in the distance, metallic banging, phone radio interference",
        "recording_date": "2019-09-23 11:24",
        "source": "upload://Alacoque_ZOOM0034_EQ.wav"
    },
    {
        "recording_start_location": "Landhies Road",
        "location_latitude": -1.2871685,
        "location_longitude": 36.83652099999995,
        "recording_route": "I am on Ladhies Road and I use the bike at a speed of 5km/hr. I got stationary for 2min then I walk down at the Jua Kali Market",
        "recording_description": "Binaural microphone",
        "recording_name": "Alacoque_ZOOM0035_EQ",
        "recording_special_sounds": "Tuktuk, motorcycle, welding and metalwork banging, people speaking Kikuyu",
        "recording_date": "2019-09-23 11:44",
        "source": "upload://Alacoque_ZOOM0035_EQ.wav"
    },
    {
        "recording_start_location": "Oloolua Primate Center",
        "location_latitude": -1.3653407,
        "location_longitude": 36.70380979999999,
        "recording_route": "walking around a stream in Oloolua Forest, swamp",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0027_EQ",
        "recording_special_sounds": "bird calls, cows mooing, camera clicking, water flowing",
        "recording_date": "2019-09-18 16:58",
        "source": "upload://ZOOM0027_EQ.wav"
    },
    {
        "recording_start_location": "Dagoz Artist Bar, Karandini Road",
        "location_latitude": -1.2994761,
        "location_longitude": 36.757742,
        "recording_route": "standing inside Dagoz Bar, at a table in the back right of the performance venue",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0030_EQ",
        "recording_special_sounds": "band playing, people talking, applause, shouting, screaming",
        "recording_date": "2019-09-18 23:11",
        "source": "upload://ZOOM0030_EQ.wav"
    },
    {
        "source": "upload://Black_ZOOM0001_EQ.wav",
        "recording_name": "Black_ZOOM0001_EQ",
        "recording_start_location": "Kenya National Theater - Harry Thuku Road",
        "location_latitude": -1.2785132,
        "location_longitude": 36.8156772,
        "recording_route": "At the Kenya National Theater, walking from the gate to the theatre space",
        "recording_description": "Binaural microphone",
        "recording_special_sounds": "Voices, security check, conga drums and poets, voices, laughter and cheering, motor sound. Short freestyle from Black. Languages: Sheng, Kiswahili.",
        "recording_date": "2019-09-12 14:23"
    },
    {
        "recording_start_location": "Mirema Highview Estate",
        "location_latitude": -1.2129941,
        "location_longitude": 36.886933,
        "recording_route": "sitting outside on a ground-floor balcony",
        "recording_description": "Binaural microphone",
        "recording_name": "Zoom0014",
        "recording_special_sounds": "Bird sounds, Cock crowing, Matatu Horns, Shuttering of doors",
        "recording_date": "2019-09-14 06:05",
        "source": "upload://Zoom0014.wav",
    },
    {
        "recording_start_location": "Mirema bus stage 44",
        "location_latitude": -1.2129573,
        "location_longitude": 36.8928845,
        "recording_route": "Standing at the bus stop, seated inside the number 44 bus in the middle left side, from Mirema to Roysambu via Kamiti Road",
        "recording_description": "Binaural microphone",
        "recording_name": "Zoom0016",
        "recording_special_sounds": "Building noise hammers hitting stones, touts shouting route/ calling out to passengers, banging on the bus door, Coughing, Car hooting, Wind in ears, Touts on the road instructing drivers out of the deadlock, Bus engine, Background Music, Conversations, Motorcycles passing by, Child mumbling, Car braking",
        "recording_date": "2019-09-14 16:37",
        "source": "upload://Zoom0016.wav"
    },
    {
        "recording_start_location": "Roysambu bus station (route 44), A2",
        "location_latitude": -1.2172643,
        "location_longitude": 36.8936972,
        "recording_route": "sitting in bus number 44, back left side, from Roysambu to Garden City Mall stage via Thika Road highway",
        "recording_description": "Binaural microphone",
        "recording_name": "Zoom0017",
        "recording_special_sounds": "Voices, Laughing, Crying, Children voice, Shaking coins in hand, Banging of bus roof/door, Shouting, Birds, Metallic Banging",
        "recording_date": "2019-09-15 13:51",
        "source": "upload://Zoom0017.wav"
    },
    {
        "recording_start_location": "KNH bus stage 32, outside Kenyatta Hospital",
        "location_latitude": -1.300687,
        "location_longitude": 36.808813,
        "recording_route": "Sitting in the bus number 32, back left side, KNH bus stage to Ngong Road, branch left to Kabarnet Road then right to Kibera Road, join Kibera drive and end at Kwa DC stage",
        "recording_description": "Binaural microphone",
        "recording_name": "Zoom0018",
        "recording_special_sounds": "Voices, Conversations, Car hooting, Revving of engines, Birds, Coughing, Phone ring, Slamming of Bus door, Wrapping paper, Bus door rattling, Child crying, Car braking, Phone conversation, Tout shouting",
        "recording_date": "2019-09-15 14:38",
        "source": "upload://Zoom0018.wav"
    },
    {
        "recording_start_location": "Kikuyu Town - Nderi Road",
        "location_latitude": -1.2368373,
        "location_longitude": 36.6622682,
        "recording_route": "Walking from Nderi Road to Powerstar Kikuyu",
        "recording_description": "Binaural microphone",
        "recording_name": "Brian_ZOOM0009_EQ",
        "recording_special_sounds": "Matatu breaking down, conversations in Kikuyu and Kiswahili, hum of trucks and PSVs on the Southern Bypass",
        "recording_date": "2019-09-12 19:12",
        "source": "upload://Brian_ZOOM0009_EQ.wav"
    },
    {
        "recording_start_location": "National Archives, Moi Avenue",
        "location_latitude": -1.2848973,
        "location_longitude": 36.8259204,
        "recording_route": "Standing at the National Archives",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0001",
        "recording_special_sounds": "A woman teaching a group of people about women issues",
        "recording_date": "2019-09-17 12:37",
        "source": "upload://ZOOM0001.wav"
    },
    {
        "recording_start_location": "Railways Bus Stop",
        "location_latitude": -1.2898733,
        "location_longitude": 36.8276937,
        "recording_route": "Walking then standing at the Railways bus stop",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0002",
        "recording_special_sounds": "touts calling the different routes, asking people to board the matatus, matatu sliding doors closing and opening, high head and bass sound of music from matatus, wistheling, motor sound, route chants of matatu routes, rongai, ngong-bypass, lenana – race course, hooting of matatus, heavy motor sound, hitting of car door/roof/side",
        "recording_date": "2019-09-17 12:52",
        "source": "upload://ZOOM0002.wav"
    },
    {
        "recording_start_location": "Railways Bus Stop",
        "location_latitude": -1.2898733,
        "location_longitude": 36.8276937,
        "recording_route": "Walking then standing at the Railways bus stop",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0003",
        "recording_special_sounds": "touts calling the different routes, asking people to board the matatus, matatu sliding doors closing and opening, high head and bass sound of music from matatus, wistheling, motor sound, route chants of matatu routes, rongai, ngong-bypass, lenana – race course, hooting of matatus, heavy motor sound, hitting of car door/roof/side",
        "recording_date": "2019-09-17 12:53",
        "source": "upload://ZOOM0003.wav"
    },
    {
        "recording_start_location": "Railways Bus Stop",
        "location_latitude": -1.2898733,
        "location_longitude": 36.8276937,
        "recording_route": "Walking then standing at the Railways bus stop",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0004",
        "recording_special_sounds": "touts calling the different routes, asking people to board the matatus, matatu sliding doors closing and opening, high head and bass sound of music from matatus, wistheling, motor sound, route chants of matatu routes, rongai, ngong-bypass, lenana – race course, hooting of matatus, heavy motor sound, hitting of car door/roof/side",
        "recording_date": "2019-09-17 12:57",
        "source": "upload://ZOOM0004.wav"
    },
    {
        "recording_start_location": "Kibera near Olympic stage",
        "location_latitude": -1.3132416,
        "location_longitude": 36.7794678,
        "recording_route": "Standing in front of a workshop",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0011",
        "recording_special_sounds": "grinding and sanding, People making jewelery from horns",
        "recording_date": "2019-09-17 16:57",
        "source": "upload://ZOOM0011.wav"
    },
    {
        "recording_start_location": "Kibera",
        "location_latitude": -1.3114845,
        "location_longitude": 36.7879475,
        "recording_route": "Walking from Soweto to Bombululu, Kiandani",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0012",
        "recording_special_sounds": "Cars, women laughing, footsteps, whistling",
        "recording_date": "2019-09-17 17:10",
        "source": "upload://ZOOM0012.wav"
    },
    {
        "recording_start_location": "Holy Family Minor Basilica - Kaunda Street",
        "location_latitude": -1.2871165,
        "location_longitude": 36.8208071,
        "recording_route": "walking from the Holy Family Basilica to city council building to Harambee Avenue and back to Basilica - (Kaunda street - Parliament road - Cityhall Way)",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0006_EQ",
        "recording_special_sounds": "car engines, birds, cars passing, footsteps on concrete, wind, hooting, voices, motorbike engine, car brakes squeaking",
        "recording_date": "2019-09-19 06:05",
        "source": "upload://ZOOM0006_EQ.wav"
    },
    {
        "recording_start_location": "Oloolua Forest - Cave",
        "location_latitude": -1.3582668,
        "location_longitude": 36.7124999,
        "recording_route": "Caves at the Oloolua Nature Trail",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamaru_cave",
        "recording_special_sounds": "footsteps, falling twigs, echoes, birds, voices",
        "recording_date": "2019-09-18 15:20",
        "source": "upload://Kamaru_cave.wav"
    },
    {
        "recording_start_location": "Oloolua Forest - Waterfall",
        "location_latitude": -1.3582668,
        "location_longitude": 36.7124999,
        "recording_route": "Waterfall at the Oloolua Nature Trail",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamaru_WalkWaterfall",
        "recording_special_sounds": "motorcycles, insects, birds, waterfall, footsteps, twigs breaking",
        "recording_date": "2019-09-18 15:30",
        "source": "upload://Kamaru_WalkWaterfall.wav"
    },
    {
        "recording_start_location": "Oloolua Forest - Pumps",
        "location_latitude": -1.3582668,
        "location_longitude": 36.7124999,
        "recording_route": "Pumps at the Oloolua Nature Trail",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamaru_pumps",
        "recording_special_sounds": "waterfall sounds, pump, spray sound",
        "recording_date": "2019-09-18 15:50",
        "source": "upload://Kamaru_pumps.wav"
    },
    {
        "recording_start_location": "Oloolua Forest - River",
        "location_latitude": -1.3582668,
        "location_longitude": 36.7124999,
        "recording_route": "River at the Oloolua Nature Trail",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamaru_WaterFlow",
        "recording_special_sounds": "water flowing over rocks",
        "recording_date": "2019-09-18 16:20",
        "source": "upload://Kamaru_WaterFlow.wav"
    },
    {
        "recording_start_location": "Oloolua Forest - Swamp",
        "location_latitude": -1.3582668,
        "location_longitude": 36.7124999,
        "recording_route": "Swamp at the Oloolua Nature Trail",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamaru_swamp",
        "recording_special_sounds": "footsteps, cracking twigs, birdsong, voices, motorcycles in the background",
        "recording_date": "2019-09-18 17:30",
        "source": "upload://Kamaru_swamp.wav"
    },
    {
        "recording_start_location": "Maasai Mbili Artists' Centre - Kibera Drive",
        "location_latitude": -1.3115472,
        "location_longitude": 36.7745376,
        "recording_route": "Walking along Kibera drive",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0019_EQ",
        "recording_special_sounds": "Drums, singing, voices, shakers, Salvation Army, Choir, engine sound, children singing, laughing, motor bike engine, wind",
        "recording_date": "2019-09-15 15:38",
        "source": "upload://ZOOM0019_EQ.wav"
    },
    {
        "recording_start_location": "The Den, Kerarapon Drive, Nairobi, Kenya",
        "location_latitude":  -1.3147755,
        "location_longitude": 36.6602178,
        "recording_route": "Sitting at the bar",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0020_EQ",
        "recording_special_sounds": "Benga music, voices, laughter, conversations in Dholuo & Sheng",
        "recording_date": "2019-09-15 15:38",
        "source": "upload://ZOOM0020_EQ.wav"
    },
    {
        "recording_start_location": "Kikuyu Market (Mini)",
        "location_latitude":  -1.2471951,
        "location_longitude": 36.6790986,
        "recording_route": "Walking: Powerstar supermarket road opposite Kikuyu Township onto the mini market, sitting down and eating fruit",
        "recording_description": "Binaural microphone",
        "recording_name": "Waringa_0003",
        "recording_special_sounds": "voices, kikuyu language, motors revving, motorbike engine, wind howling, metal clinking",
        "recording_date": "2019-09-17 14:53",
        "source": "upload://Waringa_0003.wav"
    },

    {
        "recording_start_location": "Cyber Cafe Kikuyu",
        "location_latitude":  -1.248438,
        "location_longitude": 36.664438,
        "recording_route": "Walking: on a road with shops on boths sides, up the stairs in to a cyber cafe, standing in the cyber next to the printer then corridor and out again",
        "recording_description": "Binaural microphone",
        "recording_name": "Waringa_ZOOm0004",
        "recording_special_sounds": "voices, conversations, motors revving, typing on keyboards, paper rustling, bubble wrap, radio, coughing, sound of water in the drainage, footsteps, reverberation of footsteps in staircase",
        "recording_date": "2019-09-18 15:06",
        "source": "upload://Waringa_ZOOm0004.wav"
    },
    {
        "recording_start_location": "Silanga Road, Karen",
        "location_latitude":  -1.3472172,
        "location_longitude": 36.7445694,
        "recording_route": "Walking: Silanga road to Red Brick",
        "recording_description": "Binaural microphone",
        "recording_name": "Waringa_ZOOm0005",
        "recording_special_sounds": "birds, car motors, children laughing and talking, zip being closed, footsteps, voices, wind",
        "recording_date": "2019-09-18 16:45",
        "source": "upload://Waringa_ZOOm0005.wav"
    },
    {
        "recording_start_location": "Aga Khan Walk / Kencom",
        "location_latitude":  -1.2869819,
        "location_longitude": 36.8250462,
        "recording_route": "Walking: Start at Kencom/Aga Khan Walk junction. Straight down Aga Khan walk along the side walk closer to Reinsurance Plaza. Turning around at Harambee Avenue walking back past Electricity House, Uchumi until Nkrumah Ave Street sign next to Kencom Building",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0031_1",
        "recording_special_sounds": "bus engines revving, people shouting over the buses, footsteps, rustling leaves, voices in different languages (swahili, sheng, kikuyu, kamba, luo). Preacher shouting at Kencom, People talking on phones, humming sound (air conditioners?) from Kencom Building",
        "recording_date": "2019-09-21 11:45",
        "source": "upload://ZOOM0031_1.wav"
    },
    {
        "recording_start_location": "Aga Khan Walk / Kencom",
        "location_latitude":  -1.2869819,
        "location_longitude": 36.8250462,
        "recording_route": "Walking: Start at Kencom/Aga Khan Walk junction. Straight down Aga Khan walk along the side walk closer to Reinsurance Plaza. Turning around at Harambee Avenue walking back past Electricity House, Uchumi until Nkrumah Ave Street sign next to Kencom Building",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0031_2",
        "recording_special_sounds": "birds chirping, crossing light signal (beeping; please wait), motorcycle engine, wind, laughter, child mumbling or singing, ‘welcome to measure your height weight’ from weighing scales,",
        "recording_date": "2019-09-21 11:45",
        "source": "upload://ZOOM0031_2.wav"
    },
    {
        "recording_start_location": "High Court Car Park / Maasai Market",
        "location_latitude":  -1.2920659,
        "location_longitude": 36.82194619999999,
        "recording_route": "Walking: entering at main entrance, turn to the right, until circle is completed",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0032",
        "recording_special_sounds": "voices, haggling, conversations, voices in English addressing tourists, drum beats, laughter, car alarm, footsteps, clincking cutlery, different languages (Kikuyu, English, Swahili, Kamba, Sheng), being called sister, radio broadcast music and conversation, coughing, rustling bags/packaging, plastic chairs dragging on the ground, rustling canvas paintings",
        "recording_date": "2019-09-18 12:18",
        "source": "upload://ZOOM0032.wav"
    },
    {
        "recording_start_location": "Workshop Road at Footbridge",
        "location_latitude":  -1.2939695,
        "location_longitude": 36.82705149999999,
        "recording_route": "Walking: Workshop Road (near Station Road) starting at Footbridge (crossing over the rail tracks) until the gate out of Railway Slippers next to fruit vendors. Past Factory Road but before reaching the Industrial Area Roundabout (Bunyala Rd)",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0033",
        "recording_special_sounds": "Footsteps on concrete, footsteps wooden planks ( on the bridge), bird songs, child talking, zipper, voices, commotion below the bridge ( at railway where a suspected criminal was being pursued by policeman)wind, promotion music, pre recorded seller sound (selling shoes), DJ recorded music, footsteps, live guitar sound and radio, footsteps, motor cycle sound, recorded sales sound (selling electronics, computer accessories, casio calculators, cell phones, finger print scanner), different languages ( Swahili, English, Sheng, Kamba, Kikuyu)",
        "recording_date": "2019-09-18 12:47",
        "source": "upload://ZOOM0033.wav"
    },
    {
        "recording_start_location": "Kyuna Road",
        "location_latitude":  -1.2506205,
        "location_longitude": 36.7758432,
        "recording_route": "Walking around compound in Kyuna, around two houses and into a garden",
        "recording_description": "Binaural microphone",
        "recording_name": "Lorna_ZOOM0036_EQ",
        "recording_special_sounds": "Birds, wind, dogs, cats, cars, footsteps, gate opening",
        "recording_date": "2019-10-02 18:30",
        "source": "upload://Lorna_ZOOM0036_EQ.wav"
    },
    {
        "recording_start_location": "Naivas Supermarket Donholm",
        "location_latitude":  -1.2959188,
        "location_longitude": 36.88715860000001,
        "recording_route": "voice of woman in conversation on mobile phone, Sound of TV broadcasting the Lion's den program, Phone ringing, cleaning machine, beeping of till, closing of till, tape, motor/car sound, supermarket trolly",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0007_EQ",
        "recording_special_sounds": "Birds, wind, dogs, cats, cars, footsteps, gate opening",
        "recording_date": "2019-09-12 18:14",
        "source": "upload://ZOOM0007_EQ.wav"
    },
    {
        "recording_start_location": "Mpya Pipeline Stage, Outer Ring Road",
        "location_latitude":  -1.3134119,
        "location_longitude": 36.8914469,
        "recording_route": "standing at Stage Mpya, Pipeline",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0008_EQ",
        "recording_special_sounds": "Christian Crusade, Speaker using a megaphone, aeroplane passing, feedback in megaphone, receding to Women shouting and singing, music, voices of conversations, singing",
        "recording_date": "2019-09-12 18:43",
        "source": "upload://ZOOM0008_EQ.wav"
    },
    {
        "recording_start_location": "Murram Road, AA Grounds, Catherine Ndereba",
        "location_latitude":  -1.3227864,
        "location_longitude": 36.88745649999999,
        "recording_route": "walking along Murram Road, over AA Grounds, off Catherine Ndereba Road",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0009_EQ",
        "recording_special_sounds": "footsteps on dirt road, tuk tuk horn, tuk tuk motor sound, music reggae close by, wooden planks onto each other, Karibu costumer, motor/car sounds, sneezing, laughing, squeeking of cars, coughing, plates rattling, sweeping, high heel footsteps",
        "recording_date": "2019-09-13 05:55",
        "source": "upload://ZOOM0009_EQ.wav"
    },
    {
        "recording_start_location": "Eastleigh 2nd Avenue, shop, carpet shop",
        "location_latitude":  -1.2722748,
        "location_longitude": 36.8504403,
        "recording_route": "walking along street, then into carpet shop and out again",
        "recording_description": "Binaural microphone",
        "recording_name": "ZOOM0013_EQ",
        "recording_special_sounds": "motor, cars revving engine, music beats, beeping, banging of metal/car door, motor bike engines, voices, voice from speaker/promotion voice, shouting of prices, hooting motorbike, plates klinckling, vendors calls (maji baridi), bell, street noise, inside shop, muffled  street noise, electric sowing machine in shop, voices, languages (somali)",
        "recording_date": "2019-09-13 17:11",
        "source": "upload://ZOOM0013_EQ.wav"
    },
    {
        "recording_start_location": "Nairobi River, Kirinyaga Road",
        "location_latitude":  -1.2803832,
        "location_longitude": 36.8268719,
        "recording_route": "Walking along the River",
        "recording_description": "Binaural microphone",
        "recording_name": "Kamwangi_ZOOM0010_EQ",
        "recording_special_sounds": "voices, laughter car hooting",
        "recording_date": "2019-09-20 11:50",
        "source": "upload://Kamwangi_ZOOM0010_EQ.wav"
    }
]

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

# def bulk_load_recordings(data, path="/srv/funkwhale/data/Archive"):
#     for datum in data:
#         with transaction.atomic():
#             filename = datum["source"].split("://")[1]
#             upload = models.Upload(**datum)
#             fp = os.path.join(path, filename)
#             if os.path.isfile(fp):
#                 try:
#                     with open(fp, 'rb') as recording:
#                         upload.audio_file.save(filename, File(recording), save=True)
#                     upload.save()
#                     process_upload(upload)
#                     print(f"processed {filename}")
#                 except:
#                     print(f"xxxxxxxxxxx failed at {filename}")
#             else:
#                 print(f"xxxxxxxxxxx {fp} not found")
# def process_upload(upload):                       
#     import_metadata = upload.import_metadata or {}
#     old_status = upload.import_status             
#     audio_file = upload.get_audio_file()          
#     additional_data = {}                          
#     final_metadata = upload.__dict__              
#     track = get_track_from_import_metadata(       
#         final_metadata                            
#     )                                             
#     upload.track = track                          
#     audio_data = upload.get_audio_data()          
#     if audio_data:
#         upload.duration = audio_data["duration"]
#         upload.size = audio_data["size"]
#         upload.bitrate = audio_data["bitrate"]
#         upload.import_status = "finished"
#         upload.import_date = timezone.now()
#         upload.save(
#             update_fields=[
#                 "track",
#                 "import_status",
#                 "import_date",
#                 "size",
#                 "duration",
#                 "bitrate",
#             ]
#         )

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
data = []
with open(file) as fobj:
    data_file = csv.DictReader(fobj)
    for row in data_file:
        data.append(row)
bulk_load_recordings(data, path=cur_dir)


# def write_data_to_csv(son_data):
#     with open('son_archive_data.csv', 'w') as f:
#         w = csv.DictWriter(f, son_data.keys())
#         w.writeheader()
#         w.writerow(son_data)
#
# if __name__ == "__main__":
#     write_data_to_csv(data)
