import random
import sqlite3
import asyncio
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# ================= CONFIG =================
TOKEN = "8900514648:AAG4XB90hCvKPabk-3RNAhsggQ6TTnnS0ms"
CHANNEL = "@iiv_imperya"
CREATOR = "@aazamatovc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
conn = sqlite3.connect("ielts.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    score INTEGER DEFAULT 0,
    total_tests INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_test_date TEXT DEFAULT ''
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS mistakes (
    user_id INTEGER,
    question TEXT,
    your_answer TEXT,
    correct_answer TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS duels (
    duel_id TEXT PRIMARY KEY,
    player1 INTEGER,
    player2 INTEGER,
    p1_score INTEGER DEFAULT 0,
    p2_score INTEGER DEFAULT 0,
    p1_done INTEGER DEFAULT 0,
    p2_done INTEGER DEFAULT 0,
    questions TEXT,
    status TEXT DEFAULT 'waiting'
)
""")
conn.commit()

# ================= READING QUESTIONS (with difficulty points) =================
# difficulty: 1=easy, 2=medium, 3=hard
reading_questions = [
    # Present Simple (easy=1pt)
    {"q": "She ___ to school every day.", "options": ["A) go","B) goes","C) going","D) gone"], "a": "B", "pts": 1},
    {"q": "They ___ students.", "options": ["A) is","B) are","C) am","D) be"], "a": "B", "pts": 1},
    {"q": "He ___ not like tea.", "options": ["A) do","B) does","C) is","D) are"], "a": "B", "pts": 1},
    {"q": "We ___ football every weekend.", "options": ["A) plays","B) play","C) playing","D) played"], "a": "B", "pts": 1},
    {"q": "The sun ___ in the east.", "options": ["A) rise","B) rises","C) rising","D) rose"], "a": "B", "pts": 1},
    {"q": "My father ___ a doctor.", "options": ["A) are","B) am","C) is","D) be"], "a": "C", "pts": 1},
    {"q": "Dogs ___ meat.", "options": ["A) eats","B) eat","C) eating","D) eaten"], "a": "B", "pts": 1},
    {"q": "She ___ English very well.", "options": ["A) speak","B) speaks","C) speaking","D) spoke"], "a": "B", "pts": 1},
    {"q": "I ___ coffee every morning.", "options": ["A) drinks","B) drink","C) drank","D) drinking"], "a": "B", "pts": 1},
    {"q": "He ___ to music every night.", "options": ["A) listen","B) listens","C) listening","D) listened"], "a": "B", "pts": 1},

    # Present Continuous (easy=1pt)
    {"q": "She ___ TV now.", "options": ["A) watch","B) watches","C) is watching","D) watched"], "a": "C", "pts": 1},
    {"q": "I ___ a book right now.", "options": ["A) read","B) reads","C) am reading","D) readed"], "a": "C", "pts": 1},
    {"q": "They ___ football at the moment.", "options": ["A) play","B) plays","C) are playing","D) played"], "a": "C", "pts": 1},
    {"q": "He ___ to school now.", "options": ["A) go","B) goes","C) is going","D) went"], "a": "C", "pts": 1},
    {"q": "We ___ lunch right now.", "options": ["A) eat","B) eats","C) are eating","D) ate"], "a": "C", "pts": 1},

    # Past Simple (medium=2pts)
    {"q": "I ___ to London last year.", "options": ["A) go","B) went","C) goes","D) going"], "a": "B", "pts": 2},
    {"q": "She ___ a letter yesterday.", "options": ["A) write","B) writes","C) wrote","D) written"], "a": "C", "pts": 2},
    {"q": "They ___ a movie last night.", "options": ["A) watch","B) watches","C) watched","D) watching"], "a": "C", "pts": 2},
    {"q": "He ___ his homework an hour ago.", "options": ["A) finish","B) finishes","C) finished","D) finishing"], "a": "C", "pts": 2},
    {"q": "We ___ pizza for dinner.", "options": ["A) eat","B) eats","C) ate","D) eaten"], "a": "C", "pts": 2},

    # Past Continuous (medium=2pts)
    {"q": "I ___ when you called.", "options": ["A) sleep","B) slept","C) was sleeping","D) sleeping"], "a": "C", "pts": 2},
    {"q": "They ___ football at 5pm.", "options": ["A) play","B) played","C) were playing","D) are playing"], "a": "C", "pts": 2},
    {"q": "She ___ dinner when I arrived.", "options": ["A) cook","B) cooked","C) was cooking","D) cooks"], "a": "C", "pts": 2},
    {"q": "He ___ TV when the phone rang.", "options": ["A) watch","B) watches","C) was watching","D) watched"], "a": "C", "pts": 2},
    {"q": "We ___ a walk when it started raining.", "options": ["A) take","B) took","C) were taking","D) taking"], "a": "C", "pts": 2},

    # Future Simple (medium=2pts)
    {"q": "I ___ you tomorrow.", "options": ["A) call","B) will call","C) calls","D) called"], "a": "B", "pts": 2},
    {"q": "She ___ a doctor.", "options": ["A) will be","B) is","C) was","D) be"], "a": "A", "pts": 2},
    {"q": "They ___ the match.", "options": ["A) win","B) wins","C) will win","D) won"], "a": "C", "pts": 2},
    {"q": "He ___ English next year.", "options": ["A) study","B) studies","C) will study","D) studied"], "a": "C", "pts": 2},
    {"q": "We ___ to Paris soon.", "options": ["A) travel","B) travels","C) will travel","D) traveled"], "a": "C", "pts": 2},

    # Present Perfect (medium=2pts)
    {"q": "I ___ this film before.", "options": ["A) see","B) saw","C) have seen","D) seen"], "a": "C", "pts": 2},
    {"q": "She ___ her keys.", "options": ["A) lose","B) lost","C) has lost","D) losted"], "a": "C", "pts": 2},
    {"q": "They ___ to Japan twice.", "options": ["A) go","B) went","C) have gone","D) gone"], "a": "C", "pts": 2},
    {"q": "He ___ his homework.", "options": ["A) finish","B) finished","C) has finished","D) finishing"], "a": "C", "pts": 2},
    {"q": "We ___ already ___ dinner.", "options": ["A) have / eaten","B) has / eaten","C) have / ate","D) had / eat"], "a": "A", "pts": 2},

    # Conditionals (hard=3pts)
    {"q": "If it rains, I ___ stay home.", "options": ["A) will","B) would","C) should","D) shall"], "a": "A", "pts": 3},
    {"q": "If I were rich, I ___ travel the world.", "options": ["A) will","B) would","C) should","D) could"], "a": "B", "pts": 3},
    {"q": "If she ___ harder, she would pass.", "options": ["A) study","B) studies","C) studied","D) will study"], "a": "C", "pts": 3},
    {"q": "If I had known, I ___ helped.", "options": ["A) will have","B) would have","C) should have","D) could"], "a": "B", "pts": 3},
    {"q": "If you heat water to 100°C, it ___.", "options": ["A) boil","B) boils","C) will boil","D) boiled"], "a": "B", "pts": 3},

    # Articles (easy=1pt)
    {"q": "___ apple a day keeps the doctor away.", "options": ["A) A","B) An","C) The","D) —"], "a": "B", "pts": 1},
    {"q": "I saw ___ interesting movie last night.", "options": ["A) a","B) an","C) the","D) —"], "a": "B", "pts": 1},
    {"q": "She is ___ engineer.", "options": ["A) a","B) an","C) the","D) —"], "a": "B", "pts": 1},
    {"q": "___ Nile is the longest river.", "options": ["A) A","B) An","C) The","D) —"], "a": "C", "pts": 1},
    {"q": "He plays ___ piano.", "options": ["A) a","B) an","C) the","D) —"], "a": "C", "pts": 1},

    # Prepositions (medium=2pts)
    {"q": "I was born ___ 1999.", "options": ["A) in","B) on","C) at","D) by"], "a": "A", "pts": 2},
    {"q": "She wakes up ___ 7 o'clock.", "options": ["A) in","B) on","C) at","D) by"], "a": "C", "pts": 2},
    {"q": "We met ___ Monday.", "options": ["A) in","B) on","C) at","D) by"], "a": "B", "pts": 2},
    {"q": "He lives ___ London.", "options": ["A) in","B) on","C) at","D) by"], "a": "A", "pts": 2},
    {"q": "The book is ___ the table.", "options": ["A) in","B) on","C) at","D) under"], "a": "B", "pts": 2},

    # Modal Verbs (medium=2pts)
    {"q": "You ___ smoke here.", "options": ["A) mustn't","B) needn't","C) shouldn't","D) couldn't"], "a": "A", "pts": 2},
    {"q": "She ___ speak three languages.", "options": ["A) can","B) may","C) must","D) shall"], "a": "A", "pts": 2},
    {"q": "You ___ see a doctor.", "options": ["A) should","B) shall","C) will","D) can"], "a": "A", "pts": 2},
    {"q": "___ I open the window?", "options": ["A) Will","B) Shall","C) Must","D) Should"], "a": "B", "pts": 2},
    {"q": "He ___ be at home now.", "options": ["A) might","B) will","C) shall","D) do"], "a": "A", "pts": 2},

    # Passive Voice (hard=3pts)
    {"q": "The letter ___ by Mary.", "options": ["A) write","B) wrote","C) was written","D) written"], "a": "C", "pts": 3},
    {"q": "English ___ all over the world.", "options": ["A) speak","B) spoke","C) is spoken","D) speaking"], "a": "C", "pts": 3},
    {"q": "The cake ___ by my mother.", "options": ["A) make","B) made","C) was made","D) making"], "a": "C", "pts": 3},
    {"q": "Cars ___ in factories.", "options": ["A) produce","B) produced","C) are produced","D) producing"], "a": "C", "pts": 3},
    {"q": "The window ___ by the boy.", "options": ["A) break","B) broke","C) was broken","D) breaking"], "a": "C", "pts": 3},

    # Comparatives (medium=2pts)
    {"q": "She is ___ than her sister.", "options": ["A) tall","B) taller","C) tallest","D) most tall"], "a": "B", "pts": 2},
    {"q": "This is ___ book in the library.", "options": ["A) interesting","B) more interesting","C) most interesting","D) the most interesting"], "a": "D", "pts": 2},
    {"q": "He runs ___ than I do.", "options": ["A) fast","B) faster","C) fastest","D) most fast"], "a": "B", "pts": 2},
    {"q": "That was ___ day of my life.", "options": ["A) bad","B) worse","C) worst","D) the worst"], "a": "D", "pts": 2},
    {"q": "She sings ___ than anyone I know.", "options": ["A) good","B) better","C) best","D) well"], "a": "B", "pts": 2},

    # Conjunctions (easy=1pt)
    {"q": "I like tea ___ coffee.", "options": ["A) and","B) but","C) or","D) so"], "a": "A", "pts": 1},
    {"q": "She is tired ___ she will not stop.", "options": ["A) and","B) but","C) or","D) so"], "a": "B", "pts": 1},
    {"q": "Hurry up ___ you'll miss the bus.", "options": ["A) and","B) but","C) or","D) so"], "a": "C", "pts": 1},
    {"q": "He studied hard ___ he passed.", "options": ["A) and","B) but","C) or","D) so"], "a": "D", "pts": 1},
    {"q": "___ it was raining, we went out.", "options": ["A) Although","B) Because","C) So","D) And"], "a": "A", "pts": 1},

    # Question Forms (easy=1pt)
    {"q": "___ you speak English?", "options": ["A) Are","B) Is","C) Do","D) Does"], "a": "C", "pts": 1},
    {"q": "___ she from?", "options": ["A) Where is","B) Where are","C) Where do","D) Where does"], "a": "A", "pts": 1},
    {"q": "___ did you go yesterday?", "options": ["A) What","B) Where","C) When","D) Why"], "a": "B", "pts": 1},
    {"q": "___ is your name?", "options": ["A) Who","B) What","C) Where","D) How"], "a": "B", "pts": 1},
    {"q": "___ old are you?", "options": ["A) What","B) Who","C) How","D) When"], "a": "C", "pts": 1},

    # Vocabulary (medium=2pts)
    {"q": "The opposite of 'hot' is ___.", "options": ["A) warm","B) cool","C) cold","D) mild"], "a": "C", "pts": 2},
    {"q": "A synonym of 'happy' is ___.", "options": ["A) sad","B) angry","C) joyful","D) tired"], "a": "C", "pts": 2},
    {"q": "She is very ___. She never tells lies.", "options": ["A) lazy","B) honest","C) rude","D) selfish"], "a": "B", "pts": 2},
    {"q": "The ___ of a book is its cover label.", "options": ["A) title","B) chapter","C) index","D) paragraph"], "a": "A", "pts": 2},
    {"q": "He ___ the bus and arrived late.", "options": ["A) caught","B) missed","C) took","D) drove"], "a": "B", "pts": 2},

    # Reported Speech (hard=3pts)
    {"q": 'She said, "I am tired." → She said she ___ tired.', "options": ["A) is","B) was","C) were","D) be"], "a": "B", "pts": 3},
    {"q": 'He said, "I will come." → He said he ___ come.', "options": ["A) will","B) would","C) shall","D) should"], "a": "B", "pts": 3},
    {"q": 'She asked, "Do you like it?" → She asked if I ___ it.', "options": ["A) like","B) liked","C) likes","D) liking"], "a": "B", "pts": 3},
    {"q": 'He said, "I have finished." → He said he ___ finished.', "options": ["A) has","B) have","C) had","D) having"], "a": "C", "pts": 3},
    {"q": 'She said, "I can swim." → She said she ___ swim.', "options": ["A) can","B) could","C) may","D) might"], "a": "B", "pts": 3},

    # Gerund vs Infinitive (hard=3pts)
    {"q": "I enjoy ___ music.", "options": ["A) listen","B) listens","C) listening","D) to listen"], "a": "C", "pts": 3},
    {"q": "She wants ___ a doctor.", "options": ["A) be","B) being","C) to be","D) been"], "a": "C", "pts": 3},
    {"q": "He stopped ___ cigarettes.", "options": ["A) smoke","B) to smoke","C) smoking","D) smoked"], "a": "C", "pts": 3},
    {"q": "They decided ___ early.", "options": ["A) leave","B) leaving","C) to leave","D) left"], "a": "C", "pts": 3},
    {"q": "I'm good at ___.", "options": ["A) cook","B) cooking","C) to cook","D) cooked"], "a": "B", "pts": 3},

    # Mixed Grammar (hard=3pts)
    {"q": "Neither she nor I ___ going.", "options": ["A) am","B) is","C) are","D) be"], "a": "A", "pts": 3},
    {"q": "Each of the boys ___ a prize.", "options": ["A) get","B) gets","C) got","D) getting"], "a": "B", "pts": 3},
    {"q": "The news ___ shocking.", "options": ["A) are","B) were","C) is","D) be"], "a": "C", "pts": 3},
    {"q": "There ___ no water in the bottle.", "options": ["A) are","B) were","C) is","D) be"], "a": "C", "pts": 3},
    {"q": "He as well as his friends ___ invited.", "options": ["A) are","B) were","C) was","D) is"], "a": "C", "pts": 3},
]

# ================= WRITING TOPICS =================
writing_questions = [
    {"q": "Write about the importance of education in modern life."},
    {"q": "Describe your hometown and what makes it special."},
    {"q": "Discuss the impact of technology on daily life."},
    {"q": "Write about your best friend and why you value them."},
    {"q": "Explain the benefits of playing sports."},
    {"q": "Write about climate change and its effects."},
    {"q": "Describe your favorite place and why you love it."},
    {"q": "Discuss the pros and cons of social media."},
    {"q": "Write about how to live a healthy life."},
    {"q": "Describe your dreams and goals for the future."},
    {"q": "Write about the role of family in a person's life."},
    {"q": "Discuss whether money can buy happiness."},
    {"q": "Write about the advantages of learning English."},
    {"q": "Describe a memorable trip you have taken."},
    {"q": "Write about the importance of reading books."},
    {"q": "Discuss the effects of fast food on health."},
    {"q": "Write about your favorite hobby and why you enjoy it."},
    {"q": "Describe a person who has inspired you the most."},
    {"q": "Write about the role of government in education."},
    {"q": "Discuss the advantages and disadvantages of city life."},
    {"q": "Write about how to protect the environment."},
    {"q": "Describe a challenge you overcame and what you learned."},
    {"q": "Write about the importance of time management."},
    {"q": "Discuss whether students should wear school uniforms."},
    {"q": "Write about the benefits of traveling abroad."},
    {"q": "Describe your ideal job and why you want it."},
    {"q": "Write about the impact of smartphones on teenagers."},
    {"q": "Discuss the role of women in modern society."},
    {"q": "Write about the importance of volunteering."},
    {"q": "Describe a tradition from your culture."},
]

# ================= DICTIONARY =================
dictionary = {
    "hello": "salom", "goodbye": "xayr", "thank you": "rahmat", "please": "iltimos",
    "yes": "ha", "no": "yo'q", "good": "yaxshi", "bad": "yomon", "big": "katta",
    "small": "kichik", "new": "yangi", "old": "eski / qari", "hot": "issiq",
    "cold": "sovuq", "fast": "tez", "slow": "sekin", "happy": "xursand",
    "sad": "xafa", "beautiful": "chiroyli", "ugly": "xunuk", "strong": "kuchli",
    "weak": "kuchsiz", "rich": "boy", "poor": "kambag'al", "easy": "oson",
    "difficult": "qiyin", "clean": "toza", "dirty": "iflos", "open": "ochiq",
    "closed": "yopiq", "full": "to'liq", "empty": "bo'sh", "right": "to'g'ri",
    "wrong": "noto'g'ri", "early": "erta", "late": "kech", "loud": "baland",
    "quiet": "jim", "safe": "xavfsiz", "dangerous": "xavfli", "funny": "kulgili",
    "serious": "jiddiy", "kind": "mehribon", "rude": "qo'pol", "honest": "halol",
    "lazy": "dangasa", "busy": "band", "free": "bo'sh / ozod", "tired": "charchagan",
    "hungry": "och", "thirsty": "chanqagan", "sick": "kasal", "healthy": "sog'lom",
    "smart": "aqlli", "brave": "jasur", "shy": "uyatchan", "angry": "g'azablangan",
    "scared": "qo'rqqan", "surprised": "hayron", "bored": "zerikkan",
    "excited": "hayajonlangan", "confused": "chalg'igan", "proud": "g'ururli",
    "jealous": "hasadchi", "lonely": "yolg'iz", "friendly": "do'stona",
    "patient": "sabr-toqatli", "greedy": "ochko'z", "selfish": "xudbin",
    "generous": "saxiy", "polite": "odobli", "careful": "ehtiyotkor",
    "careless": "beparvo", "lucky": "omadli", "unlucky": "baxtsiz",
    "famous": "mashhur", "important": "muhim", "useless": "befoyda",
    "useful": "foydali", "necessary": "zarur", "impossible": "imkonsiz",
    "possible": "mumkin", "real": "haqiqiy", "fake": "soxta",
    "modern": "zamonaviy", "ancient": "qadimiy", "local": "mahalliy",
    "foreign": "xorijiy", "national": "milliy", "international": "xalqaro",
    "natural": "tabiiy", "artificial": "sun'iy", "human": "inson",
    "animal": "hayvon", "plant": "o'simlik", "tree": "daraxt", "flower": "gul",
    "grass": "o't", "water": "suv", "fire": "olov", "earth": "yer", "air": "havo",
    "sky": "osmon", "sun": "quyosh", "moon": "oy", "star": "yulduz",
    "cloud": "bulut", "rain": "yomg'ir", "snow": "qor", "wind": "shamol",
    "storm": "bo'ron", "mountain": "tog'", "river": "daryo", "lake": "ko'l",
    "sea": "dengiz", "ocean": "okean", "island": "orol", "forest": "o'rmon",
    "desert": "cho'l", "valley": "vodiy", "field": "dala", "garden": "bog'",
    "city": "shahar", "village": "qishloq", "country": "mamlakat", "world": "dunyo",
    "street": "ko'cha", "road": "yo'l", "bridge": "ko'prik", "building": "bino",
    "house": "uy", "room": "xona", "door": "eshik", "window": "deraza",
    "floor": "pol / qavat", "wall": "devor", "ceiling": "ship", "roof": "tom",
    "kitchen": "oshxona", "bedroom": "yotoqxona", "bathroom": "hammom",
    "school": "maktab", "university": "universitet", "hospital": "kasalxona",
    "shop": "do'kon", "market": "bozor", "bank": "bank", "hotel": "mehmonxona",
    "restaurant": "restoran", "library": "kutubxona", "museum": "muzey",
    "mosque": "masjid", "airport": "aeroport", "station": "stansiya",
    "office": "ofis", "factory": "zavod", "farm": "ferma",
    "car": "mashina", "bus": "avtobus", "train": "poyezd", "plane": "samolyot",
    "ship": "kema", "bicycle": "velosiped", "motorcycle": "mototsikl",
    "truck": "yuk mashinasi", "taxi": "taksi", "boat": "qayiq",
    "book": "kitob", "pen": "ruchka", "pencil": "qalam", "paper": "qog'oz",
    "notebook": "daftar", "bag": "sumka", "chair": "stul", "table": "stol",
    "bed": "karavot", "sofa": "divan", "lamp": "chiroq", "clock": "soat",
    "phone": "telefon", "computer": "kompyuter", "television": "televizor",
    "key": "kalit", "lock": "qulf", "glass": "stakan / shisha", "cup": "piyola",
    "plate": "likopcha", "knife": "pichoq", "fork": "vilka", "spoon": "qoshiq",
    "bottle": "shisha", "box": "quti", "umbrella": "soyabon", "mirror": "oyna",
    "soap": "sovun", "towel": "sochiq", "clothes": "kiyim", "shirt": "ko'ylak",
    "trousers": "shim", "dress": "ko'ylak", "shoes": "poyabzal", "hat": "shlyapa",
    "coat": "palto", "jacket": "kurta", "gloves": "qo'lqop", "scarf": "sharf",
    "belt": "kamar", "ring": "uzuk", "watch": "qo'l soati", "money": "pul",
    "coin": "tanga", "price": "narx", "food": "ovqat", "bread": "non",
    "rice": "guruch", "meat": "go'sht", "fish": "baliq", "egg": "tuxum",
    "milk": "sut", "butter": "sariyog'", "cheese": "pishloq", "sugar": "shakar",
    "salt": "tuz", "oil": "yog'", "fruit": "meva", "vegetable": "sabzavot",
    "apple": "olma", "orange": "apelsin", "banana": "banan", "grape": "uzum",
    "melon": "qovun", "watermelon": "tarvuz", "tomato": "pomidor",
    "potato": "kartoshka", "onion": "piyoz", "carrot": "sabzi", "tea": "choy",
    "coffee": "qahva", "juice": "sharbat", "soup": "sho'rva", "cake": "tort",
    "candy": "konfet", "chocolate": "shokolad", "body": "tana", "head": "bosh",
    "face": "yuz", "eye": "ko'z", "ear": "quloq", "nose": "burun",
    "mouth": "og'iz", "tooth": "tish", "tongue": "til", "lip": "lab",
    "hair": "soch", "neck": "bo'yin", "shoulder": "yelka", "arm": "qo'l",
    "hand": "qo'l (kaft)", "finger": "barmoq", "leg": "oyoq",
    "foot": "oyoq (taban)", "knee": "tizza", "back": "orqa", "chest": "ko'krak",
    "stomach": "qorin", "heart": "yurak", "blood": "qon", "bone": "suyak",
    "skin": "teri", "brain": "miya", "father": "ota", "mother": "ona",
    "son": "o'g'il", "daughter": "qiz", "brother": "aka / uka",
    "sister": "opa / singil", "husband": "er", "wife": "xotin",
    "grandfather": "buva / bobo", "grandmother": "buvi / momо",
    "uncle": "amaki / tog'a", "aunt": "xola / amma", "friend": "do'st",
    "enemy": "dushman", "neighbor": "qo'shni", "teacher": "o'qituvchi",
    "student": "talaba / o'quvchi", "doctor": "shifokor", "nurse": "hamshira",
    "lawyer": "advokat", "engineer": "muhandis", "scientist": "olim",
    "artist": "rassom", "musician": "musiqachi", "writer": "yozuvchi",
    "actor": "aktyor", "singer": "qo'shiqchi", "soldier": "askar",
    "police": "politsiya", "driver": "haydovchi", "farmer": "dehqon",
    "cook": "oshpaz", "pilot": "uchuvchi", "journalist": "jurnalist",
    "businessman": "tadbirkor", "manager": "menejer",
    "one": "bir", "two": "ikki", "three": "uch", "four": "to'rt", "five": "besh",
    "six": "olti", "seven": "yetti", "eight": "sakkiz", "nine": "to'qqiz",
    "ten": "o'n", "hundred": "yuz", "thousand": "ming", "million": "million",
    "Monday": "Dushanba", "Tuesday": "Seshanba", "Wednesday": "Chorshanba",
    "Thursday": "Payshanba", "Friday": "Juma", "Saturday": "Shanba",
    "Sunday": "Yakshanba", "January": "Yanvar", "February": "Fevral",
    "March": "Mart", "April": "Aprel", "May": "May", "June": "Iyun",
    "July": "Iyul", "August": "Avgust", "September": "Sentabr",
    "October": "Oktabr", "November": "Noyabr", "December": "Dekabr",
    "morning": "ertalab", "afternoon": "tushdan keyin", "evening": "kechqurun",
    "night": "tun", "today": "bugun", "yesterday": "kecha", "tomorrow": "ertaga",
    "week": "hafta", "month": "oy", "year": "yil", "hour": "soat",
    "minute": "minut", "second": "sekund", "time": "vaqt", "always": "doim",
    "never": "hech qachon", "often": "ko'pincha", "sometimes": "ba'zan",
    "usually": "odatda", "now": "hozir", "soon": "tez orada",
    "already": "allaqachon", "still": "hali ham", "yet": "hali", "again": "yana",
    "together": "birga", "alone": "yolg'iz", "here": "bu yerda",
    "there": "u yerda", "where": "qayerda", "when": "qachon",
    "why": "nima uchun", "how": "qanday", "what": "nima", "who": "kim",
    "much": "ko'p", "many": "ko'p (son)", "few": "kam", "enough": "yetarli",
    "more": "ko'proq", "less": "kamroq", "very": "juda", "almost": "deyarli",
    "only": "faqat", "also": "ham", "even": "hatto", "just": "shunchaki",
    "because": "chunki", "although": "garchi", "if": "agar", "while": "paytida",
    "before": "oldin", "after": "keyin", "until": "gacha", "since": "dan beri",
    "during": "davomida", "above": "ustida", "below": "ostida",
    "between": "orasida", "behind": "orqasida", "beside": "yonida",
    "near": "yaqin", "far": "uzoq", "inside": "ichida", "outside": "tashqarida",
    "speak": "gapirmoq", "say": "demoq", "tell": "aytmoq", "ask": "so'ramoq",
    "answer": "javob bermoq", "write": "yozmoq", "read": "o'qimoq",
    "listen": "tinglаmoq", "hear": "eshitmoq", "see": "ko'rmoq",
    "look": "qarаmoq", "find": "topmoq", "lose": "yo'qotmoq", "give": "bermoq",
    "take": "olmoq", "bring": "keltirmoq", "put": "qo'ymoq", "get": "olmoq",
    "make": "yasаmoq", "do": "qilmoq", "go": "bormoq", "come": "kelmoq",
    "leave": "ketmoq", "arrive": "yetib kelmoq", "return": "qaytmoq",
    "stay": "qolmoq", "run": "yugurmoq", "walk": "yurmoq", "sit": "o'tirmoq",
    "stand": "turmoq", "sleep": "uxlamoq", "wake": "uyg'onmoq", "eat": "yemoq",
    "drink": "ichmoq", "buy": "sotib olmoq", "sell": "sotmoq", "pay": "to'lamoq",
    "save": "tejаmoq", "help": "yordam bermoq", "use": "ishlatmoq",
    "learn": "o'rganmoq", "teach": "o'qitmoq", "study": "o'qimoq",
    "work": "ishlаmoq", "play": "o'ynamoq", "sing": "qo'shiq aytmoq",
    "dance": "raqsga tushmoq", "draw": "chizmoq", "build": "qurmoq",
    "break": "sindirgmoq", "fix": "tuzаtmoq", "clean": "tozalаmoq",
    "wash": "yuvmoq", "change": "o'zgartirmoq", "choose": "tanlаmoq",
    "decide": "qaror qilmoq", "think": "o'ylamoq", "know": "bilmoq",
    "understand": "tushunmoq", "remember": "eslamoq", "forget": "unutmoq",
    "try": "urinmoq", "want": "xohlаmoq", "need": "kerak bo'lmoq",
    "like": "yoqtirmoq", "love": "sevmoq", "hate": "yomon ko'rmoq",
    "hope": "umid qilmoq", "believe": "ishonmoq", "agree": "rozi bo'lmoq",
    "wait": "kutmoq", "meet": "uchrashmoq", "visit": "tashrif buyurmoq",
    "call": "qo'ng'iroq qilmoq", "send": "yubormoq", "show": "ko'rsatmoq",
    "explain": "tushuntirgmoq", "suggest": "taklif qilmoq",
    "promise": "va'da bermoq", "accept": "qabul qilmoq", "reject": "rad qilmoq",
    "apologize": "uzr so'ramoq", "thank": "minnatdorlik bildirmoq",
    "celebrate": "nishonlаmoq", "enjoy": "zavqlаnmoq", "worry": "tashvishlаnmoq",
    "relax": "dam olmoq", "travel": "sayohat qilmoq", "fly": "uchmoq",
    "swim": "suzmoq", "jump": "sakramoq", "fall": "yiqilmoq", "hit": "urmoq",
    "catch": "ushlamoq", "throw": "otmoq", "carry": "ko'tarmoq",
    "cut": "kesmoq", "pour": "quymoq", "fill": "to'ldirmoq",
    "grow": "o'smoq", "plant": "ekmoq", "destroy": "yo'q qilmoq",
    "protect": "himoya qilmoq", "win": "yutmoq", "compete": "musobaqa qilmoq",
    "practice": "mashq qilmoq", "improve": "yaxshilаshmoq",
    "develop": "rivojlаnmoq", "increase": "oshmoq", "decrease": "kamaymoq",
    "continue": "davom ettirmoq", "stop": "to'xtatmoq", "begin": "boshlаnmoq",
    "end": "tugаmoq", "happen": "sodir bo'lmoq", "cause": "sabab bo'lmoq",
    "create": "yaratmoq", "produce": "ishlab chiqarmoq", "plan": "rejalashtirmoq",
    "prepare": "tayyorlаmoq", "manage": "boshqarmoq", "control": "nazorat qilmoq",
    "lead": "boshchilik qilmoq", "follow": "ergashmoq", "respect": "hurmat qilmoq",
    "support": "qo'llab-quvvatlаmoq", "inspire": "ilhomlantirgmoq",
    "solve": "yechmoq", "discover": "kashf etmoq", "invent": "ixtiro qilmoq",
    "test": "sinamoq", "measure": "o'lchаmoq", "compare": "taqqoslаmoq",
    "prove": "isbotlаmoq", "research": "tadqiq qilmoq",
    "success": "muvaffaqiyat", "failure": "muvaffaqiyatsizlik", "mistake": "xato",
    "problem": "muammo", "solution": "yechim", "idea": "fikr",
    "question": "savol", "information": "ma'lumot", "knowledge": "bilim",
    "education": "ta'lim", "experience": "tajriba", "skill": "ko'nikma",
    "ability": "qobiliyat", "talent": "iste'dod", "opportunity": "imkoniyat",
    "choice": "tanlov", "decision": "qaror", "goal": "maqsad", "dream": "orzu",
    "advice": "maslahat", "warning": "ogohlantirish", "promise": "va'da",
    "agreement": "kelishuv", "law": "qonun", "right": "huquq", "duty": "burch",
    "freedom": "erkinlik", "justice": "adolat", "peace": "tinchlik",
    "war": "urush", "conflict": "mojarо", "competition": "musobaqa",
    "cooperation": "hamkorlik", "language": "til", "culture": "madaniyat",
    "tradition": "an'ana", "history": "tarix", "science": "fan",
    "mathematics": "matematika", "physics": "fizika", "chemistry": "kimyo",
    "biology": "biologiya", "literature": "adabiyot", "music": "musiqa",
    "sport": "sport", "art": "san'at", "technology": "texnologiya",
    "internet": "internet", "data": "ma'lumotlar", "system": "tizim",
    "energy": "energiya", "power": "quvvat", "electricity": "elektr",
    "light": "yorug'lik", "sound": "ovoz", "speed": "tezlik",
    "weight": "og'irlik", "size": "o'lcham", "distance": "masofa",
    "colour": "rang", "red": "qizil", "blue": "ko'k", "green": "yashil",
    "yellow": "sariq", "white": "oq", "black": "qora", "brown": "jigarrang",
    "orange": "to'q sariq", "purple": "binafsha", "pink": "pushti",
    "grey": "kulrang", "gold": "oltin", "silver": "kumush",
}

# ================= WORD GAME DATA =================
word_game_words = [
    {"word": "APPLE", "hint": "🍎 Meva, qizil yoki yashil bo'ladi"},
    {"word": "HOUSE", "hint": "🏠 Odamlar yashaydi"},
    {"word": "WATER", "hint": "💧 Ichimlik, rangsiz suyuqlik"},
    {"word": "HAPPY", "hint": "😊 Xursandchilik hissi"},
    {"word": "MUSIC", "hint": "🎵 Quloqqa yoqadigan tovushlar"},
    {"word": "BREAD", "hint": "🍞 Nondan yasalgan"},
    {"word": "PHONE", "hint": "📱 Aloqa qurilmasi"},
    {"word": "TRAIN", "hint": "🚂 Relsda yuguradi"},
    {"word": "SMILE", "hint": "😄 Yuzda ko'rinadigan"},
    {"word": "NIGHT", "hint": "🌙 Kunduz kunning aksi"},
    {"word": "LIGHT", "hint": "💡 Qorong'uni yorita"},
    {"word": "EARTH", "hint": "🌍 Biz yashaydigan sayyora"},
    {"word": "SUGAR", "hint": "🍭 Choyga solinadigan shirin narsa"},
    {"word": "RIVER", "hint": "🏞️ Tog'dan oqib keladigan suv"},
    {"word": "CLOUD", "hint": "☁️ Osmonda suzadi"},
    {"word": "CHAIR", "hint": "🪑 Unga o'tiriladi"},
    {"word": "CLOCK", "hint": "🕐 Vaqtni ko'rsatadi"},
    {"word": "PAPER", "hint": "📄 Yozish uchun ishlatiladigan"},
    {"word": "MONEY", "hint": "💰 Narx to'lash uchun kerak"},
    {"word": "TIGER", "hint": "🐯 Yo'l-yo'l yirtqich hayvon"},
    {"word": "OCEAN", "hint": "🌊 Eng katta suv havzasi"},
    {"word": "SWORD", "hint": "⚔️ Qadimiy qurol"},
    {"word": "DREAM", "hint": "💭 Uxlaganda ko'riladi"},
    {"word": "GLASS", "hint": "🥛 Suv ichiladigan idish"},
    {"word": "HORSE", "hint": "🐴 Ot — mingib yuriladi"},
    {"word": "BRAIN", "hint": "🧠 Fikrlash a'zosi"},
    {"word": "FLAME", "hint": "🔥 Olovning ko'rinishi"},
    {"word": "STORM", "hint": "⛈️ Kuchli yomg'ir va shamol"},
    {"word": "BEACH", "hint": "🏖️ Dengiz qirg'og'i"},
    {"word": "BLOOD", "hint": "🩸 Tomirda oqadi, qizil rangli"},
]

# ================= WRITING CRITERIA =================
writing_criteria = {
    "task_achievement": {
        "name": "Task Achievement",
        "description": "Topshiriqni to'liq bajarganmi?",
        "checks": ["mavzu", "fikr", "misol", "xulosa"]
    },
    "coherence": {
        "name": "Coherence & Cohesion",
        "description": "Bog'lanish va mantiq",
        "checks": ["however", "therefore", "furthermore", "in conclusion", "firstly", "secondly", "finally", "moreover", "in addition", "for example", "for instance", "such as", "although", "despite", "because", "since", "while"]
    },
    "lexical": {
        "name": "Lexical Resource",
        "description": "So'z boyligi",
    },
    "grammar": {
        "name": "Grammatical Range",
        "description": "Grammatik to'g'rilik",
    }
}

# ================= STATE =================
state = {}
duel_waiting = {}  # username -> uid mapping for duel requests

QUESTION_TIME = 15  # seconds per question
timer_tasks = {}

# ================= MENU =================
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Reading"), KeyboardButton(text="✍️ Writing")],
        [KeyboardButton(text="📖 Dictionary"), KeyboardButton(text="🎲 Random Word")],
        [KeyboardButton(text="🏆 Leaderboard"), KeyboardButton(text="❌ My Mistakes")],
        [KeyboardButton(text="⚔️ Duel"), KeyboardButton(text="🎮 Word Game")],
        [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="💡 Daily Word")],
        [KeyboardButton(text="ℹ️ Help")]
    ],
    resize_keyboard=True
)

# ================= HELPERS =================
def get_band(score, total_pts):
    ratio = score / total_pts if total_pts > 0 else 0
    band = round(ratio * 9, 1)
    return band

def get_level(band):
    if band >= 8.0:
        return "🌟 Expert — Ajoyib natija!"
    elif band >= 7.0:
        return "🔥 Advanced — Zo'r!"
    elif band >= 6.0:
        return "👍 Upper-Intermediate — Yaxshi!"
    elif band >= 5.0:
        return "📈 Intermediate — Rivojlanmoqdasiz"
    elif band >= 4.0:
        return "💪 Elementary — Ko'proq mashq qiling"
    else:
        return "📖 Beginner — Boshlang'ich daraja"

def get_pts_label(pts):
    if pts == 1:
        return "⭐ (1 ball)"
    elif pts == 2:
        return "⭐⭐ (2 ball)"
    else:
        return "⭐⭐⭐ (3 ball)"

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

def ensure_user(uid, username=""):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)", (uid, username, 0, 0, 0, ""))
    conn.commit()

async def cancel_timer(uid):
    task = timer_tasks.pop(uid, None)
    if task:
        task.cancel()

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    ok = await check_sub(message.from_user.id)
    if not ok:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL[1:]}")]
        ])
        await message.answer("❌ Avval kanalga obuna bo'ling:", reply_markup=kb)
        return

    uid = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    ensure_user(uid, username)

    await message.answer(
        f"🎓 <b>IELTS BOT ga xush kelibsiz!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Reading</b> — Grammatika testlari (⏱15 sek)\n"
        f"✍️ <b>Writing</b> — Esse yozish + avtomatik baho\n"
        f"📖 <b>Dictionary</b> — 1000+ inglizcha-o'zbekcha so'z\n"
        f"⚔️ <b>Duel</b> — Do'stingiz bilan musobaqa!\n"
        f"🎮 <b>Word Game</b> — So'z topish o'yini\n"
        f"💡 <b>Daily Word</b> — Kunlik yangi so'z\n"
        f"🏆 <b>Leaderboard</b> — Top 10 o'quvchilar\n"
        f"📊 <b>My Stats</b> — Shaxsiy statistika\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏅 Ball tizimi:\n"
        f"⭐ Oson savol = 1 ball\n"
        f"⭐⭐ O'rta savol = 2 ball\n"
        f"⭐⭐⭐ Qiyin savol = 3 ball\n\n"
        f"👨‍💻 Yaratuvchi: {CREATOR}",
        reply_markup=menu,
        parse_mode="HTML"
    )

# ================= HELP =================
@dp.message(F.text == "ℹ️ Help")
async def help_cmd(message: Message):
    await message.answer(
        "📋 <b>BUYRUQLAR:</b>\n\n"
        "<code>/dict apple</code> — so'z tarjimasi\n"
        "<code>/random_word</code> — tasodifiy so'z\n"
        "<code>/duel @username</code> — duel chaqirish\n"
        "<code>/stats</code> — statistika\n"
        "<code>/streak</code> — ketma-ket kunlar\n\n"
        "⏱ <b>Har bir savol uchun 15 sekund vaqt beriladi!</b>\n"
        "Vaqt tugasa, savol o'tkazib yuboriladi.",
        parse_mode="HTML"
    )

# ================= SEND READING QUESTION =================
async def send_q(message: Message, uid):
    s = state.get(uid)
    if not s:
        return
    q = s["questions"][s["index"]]
    pts_label = get_pts_label(q.get("pts", 1))
    # Escape HTML special chars in question text to avoid parse errors
    q_text = q['q'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = f"❓ <b>Savol {s['index'] + 1}/{len(s['questions'])}</b> {pts_label}\n\n{q_text}"

    if s["section"] in ("reading", "duel"):
        safe_options = [opt.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;') for opt in q["options"]]
        text += "\n\n" + "\n".join(safe_options)
        text += "\n\n⏱ <b>15 sekund!</b>"
        cb_prefix = "ans" if s["section"] == "reading" else "dans"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="A", callback_data=f"{cb_prefix}_A"),
                InlineKeyboardButton(text="B", callback_data=f"{cb_prefix}_B"),
            ],
            [
                InlineKeyboardButton(text="C", callback_data=f"{cb_prefix}_C"),
                InlineKeyboardButton(text="D", callback_data=f"{cb_prefix}_D"),
            ]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        text += "\n\n<i>(Javobingizni yozing — kamida 3 gap)</i>\n⏱ <b>60 sekund!</b>"
        await message.answer(text, parse_mode="HTML")

    # Start timer
    await cancel_timer(uid)
    timeout = 15 if s["section"] in ("reading", "duel") else 60
    task = asyncio.create_task(question_timer(uid, timeout, message))
    timer_tasks[uid] = task

async def question_timer(uid, timeout, message):
    await asyncio.sleep(timeout)
    s = state.get(uid)
    if not s:
        return

    q = s["questions"][s["index"]]
    s["index"] += 1
    s["timeouts"] = s.get("timeouts", 0) + 1

    if s["section"] == "reading":
        correct_option = next((opt for opt in q['options'] if opt.startswith(q['a'] + ')')), q['a'])
        await message.answer(f"⏰ <b>Vaqt tugadi!</b>\n✅ To'g'ri javob: <b>{correct_option}</b>", parse_mode="HTML")
        cur.execute("INSERT INTO mistakes VALUES (?,?,?,?)", (uid, q["q"], "⏰ Vaqt", q["a"]))
        conn.commit()

    if s["index"] < len(s["questions"]):
        await asyncio.sleep(1)
        await send_q(message, uid)
    else:
        await finish(message, uid)

# ================= START TEST =================
@dp.message(F.text.in_(["📚 Reading", "✍️ Writing"]))
async def start_test(message: Message):
    ok = await check_sub(message.from_user.id)
    if not ok:
        return await message.answer("❌ Kanalga obuna bo'ling")

    uid = message.from_user.id
    section = "reading" if "Reading" in message.text else "writing"
    pool = reading_questions if section == "reading" else writing_questions
    selected = random.sample(pool, 10)

    state[uid] = {
        "section": section,
        "index": 0,
        "questions": selected,
        "score": 0,
        "max_pts": sum(q.get("pts", 1) for q in selected) if section == "reading" else 10,
        "start_time": time.time(),
        "answers": [],
        "timeouts": 0,
        "correct": 0,
        "wrong": 0,
    }

    section_name = "Reading 📚" if section == "reading" else "Writing ✍️"
    max_pts = state[uid]["max_pts"]
    await message.answer(
        f"🚀 <b>{section_name} testi boshlandi!</b>\n\n"
        f"📝 Jami: 10 ta savol\n"
        f"🏆 Maksimal ball: {max_pts}\n"
        f"⏱ Har savolga: {'15 sek' if section == 'reading' else '60 sek'}\n\n"
        f"💪 Omad tilaymiz!",
        parse_mode="HTML"
    )
    await send_q(message, uid)

# ================= ANSWER READING =================
@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: CallbackQuery):
    uid = callback.from_user.id
    s = state.get(uid)

    if not s or s["section"] != "reading":
        return await callback.answer("Test topilmadi. /start bosing", show_alert=True)

    await cancel_timer(uid)

    chosen = callback.data.split("_")[1]
    q = s["questions"][s["index"]]
    pts = q.get("pts", 1)

    # Inline tugmalarni o'chirib qo'yish (dublikat javob oldini olish)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    if chosen == q["a"]:
        s["score"] += pts
        s["correct"] += 1
        await callback.answer("✅ To'g'ri!")
        await callback.message.answer(
            f"✅ <b>To'g'ri javob!</b> +{pts} ball 🎉\n"
            f"📌 Javob: <b>{q['a']}</b>",
            parse_mode="HTML"
        )
    else:
        s["wrong"] += 1
        # To'g'ri variantni to'liq matnda ko'rsatish
        correct_option = next((opt for opt in q["options"] if opt.startswith(q["a"] + ")")), q["a"])
        await callback.answer("❌ Noto'g'ri!")
        await callback.message.answer(
            f"❌ <b>Noto'g'ri!</b>\n\n"
            f"Siz: <b>{chosen}</b>\n"
            f"✅ To'g'ri javob: <b>{correct_option}</b>",
            parse_mode="HTML"
        )
        cur.execute("INSERT INTO mistakes VALUES (?,?,?,?)", (uid, q["q"], chosen, q["a"]))
        conn.commit()

    s["index"] += 1

    # Mid-test feedback every 5 questions
    if s["index"] == 5:
        await callback.message.answer(
            f"📊 <b>Yarim yo'l!</b>\n"
            f"✅ To'g'ri: {s['correct']} | ❌ Noto'g'ri: {s['wrong']}\n"
            f"🏆 Ball: {s['score']}/{s['max_pts']}\n\n"
            f"Davom eting! 💪",
            parse_mode="HTML"
        )

    if s["index"] < len(s["questions"]):
        await send_q(callback.message, uid)
    else:
        await finish(callback.message, uid)

# ================= ANSWER WRITING =================
@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_([
    "📚 Reading", "✍️ Writing", "📖 Dictionary", "🎲 Random Word",
    "🏆 Leaderboard", "❌ My Mistakes", "⚔️ Duel",
    "🎮 Word Game", "📊 My Stats", "💡 Daily Word", "ℹ️ Help"
]))
async def writing_answer(message: Message):
    uid = message.from_user.id
    s = state.get(uid)

    # Word game answer
    g = state.get(f"game_{uid}")
    if g:
        await check_word_game(message, uid, g)
        return

    if not s or s["section"] != "writing":
        return

    await cancel_timer(uid)

    text = message.text.strip()
    word_count = len(text.split())
    s["answers"].append(text)
    s["index"] += 1

    writing_score = evaluate_writing(text)
    s["score"] += writing_score

    feedback = f"✅ <b>Qabul qilindi!</b> ({word_count} so'z)\n"
    if word_count < 50:
        feedback += "💡 Ko'proq yozing — kamida 150 so'z tavsiya etiladi."
    elif word_count < 150:
        feedback += "📝 Yaxshi boshlash! Ko'proq detal qo'shing."
    else:
        feedback += f"🌟 Zo'r! +{writing_score} ball"

    if s["index"] < len(s["questions"]):
        await message.answer(feedback, parse_mode="HTML")
        await send_q(message, uid)
    else:
        await message.answer(feedback, parse_mode="HTML")
        await finish(message, uid)

def evaluate_writing(text):
    """Simple writing evaluator (0-10 points per answer)"""
    score = 0
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)

    # Word count scoring (0-4 pts)
    if word_count >= 250:
        score += 4
    elif word_count >= 150:
        score += 3
    elif word_count >= 80:
        score += 2
    elif word_count >= 40:
        score += 1

    # Cohesion words (0-3 pts)
    cohesion = ["however", "therefore", "furthermore", "in conclusion",
                "firstly", "secondly", "finally", "moreover",
                "in addition", "for example", "for instance",
                "although", "despite", "because", "since",
                "on the other hand", "in contrast", "as a result"]
    cohesion_count = sum(1 for w in cohesion if w in text_lower)
    score += min(cohesion_count, 3)

    # Sentence variety (0-2 pts)
    sentences = text.split(".")
    if len(sentences) >= 5:
        score += 2
    elif len(sentences) >= 3:
        score += 1

    # Vocabulary variety (0-1 pt)
    unique_words = set(text_lower.split())
    if len(unique_words) > 40:
        score += 1

    return min(score, 10)

def get_writing_band(score, total):
    ratio = score / total if total > 0 else 0
    if ratio >= 0.85:
        return 8.0, "Excellent ✨"
    elif ratio >= 0.70:
        return 7.0, "Good 👍"
    elif ratio >= 0.55:
        return 6.0, "Competent 📈"
    elif ratio >= 0.40:
        return 5.0, "Modest 💪"
    else:
        return 4.0, "Limited — Ko'proq mashq qiling 📖"

# ================= FINISH =================
async def finish(message: Message, uid):
    await cancel_timer(uid)
    s = state[uid]
    total = len(s["questions"])
    elapsed = round(time.time() - s["start_time"])
    minutes = elapsed // 60
    seconds = elapsed % 60

    if s["section"] == "reading":
        score = s["score"]
        max_pts = s["max_pts"]
        band = get_band(score, max_pts)
        level = get_level(band)
        correct = s["correct"]
        wrong = s["wrong"]
        timeouts = s.get("timeouts", 0)

        ensure_user(uid)
        cur.execute("UPDATE users SET score = score + ?, total_tests = total_tests + 1 WHERE user_id = ?", (score, uid))
        conn.commit()

        await message.answer(
            f"🏁 <b>Test yakunlandi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ To'g'ri: <b>{correct}/{total}</b>\n"
            f"❌ Noto'g'ri: <b>{wrong}</b>\n"
            f"⏰ Vaqt tugagan: <b>{timeouts}</b>\n"
            f"🏆 Ball: <b>{score}/{max_pts}</b>\n"
            f"📊 Band: <b>{band}</b>\n"
            f"🎯 Daraja: {level}\n"
            f"⏱ Vaqt: {minutes} daq {seconds} sek\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{'🎉 Tabriklaymiz!' if band >= 7 else '📚 Ko\'proq mashq qiling!'}\n\n"
            f"👨‍💻 {CREATOR}",
            parse_mode="HTML"
        )

    else:  # Writing
        score = s["score"]
        answered = len(s["answers"])
        max_total = total * 10
        band, band_label = get_writing_band(score, max_total)

        ensure_user(uid)
        cur.execute("UPDATE users SET score = score + ?, total_tests = total_tests + 1 WHERE user_id = ?", (score, uid))
        conn.commit()

        await message.answer(
            f"🏁 <b>Writing testi yakunlandi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ Yozilgan: <b>{answered}/{total}</b>\n"
            f"🏆 Umumiy ball: <b>{score}/{max_total}</b>\n"
            f"📊 Band: <b>{band}</b>\n"
            f"🎯 Daraja: <b>{band_label}</b>\n"
            f"⏱ Vaqt: {minutes} daq {seconds} sek\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 <b>Baholash mezoni:</b>\n"
            f"• So'z soni (150+ tavsiya)\n"
            f"• Bog'lovchi so'zlar (however, therefore...)\n"
            f"• Gap turlanishi\n"
            f"• So'z boyligi\n\n"
            f"👨‍💻 {CREATOR}",
            parse_mode="HTML"
        )

    state.pop(uid, None)

# ================= DICTIONARY =================
@dp.message(F.text == "📖 Dictionary")
async def dictionary_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Tasodifiy so'z", callback_data="random_word_btn")],
        [InlineKeyboardButton(text="💡 Kunlik so'z", callback_data="daily_word_btn")],
    ])
    await message.answer(
        "📖 <b>Lug'at (1000+ so'z)</b>\n\n"
        "🔍 So'z izlash:\n"
        "👉 <code>/dict apple</code> → olma\n"
        "👉 <code>/dict salom</code> → hello (teskari)\n\n"
        "Yoki quyidagi tugmalardan foydalaning 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "random_word_btn")
async def random_word_btn(callback: CallbackQuery):
    word = random.choice(list(dictionary.keys()))
    await callback.message.answer(
        f"🎲 <b>Tasodifiy so'z:</b>\n\n"
        f"📝 <b>{word}</b> → <code>{dictionary[word]}</code>\n\n"
        f"💡 Bu so'zni eslab qoling!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "daily_word_btn")
async def daily_word_btn(callback: CallbackQuery):
    today = time.strftime("%Y%m%d")
    random.seed(int(today))
    word = random.choice(list(dictionary.keys()))
    random.seed()
    await callback.message.answer(
        f"💡 <b>Kunlik so'z — {time.strftime('%d.%m.%Y')}</b>\n\n"
        f"🔤 <b>{word.upper()}</b>\n"
        f"🇺🇿 <code>{dictionary[word]}</code>\n\n"
        f"📌 Bu so'zni bugun 5 marta ishlating!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(F.text.startswith("/dict"))
async def search_dict(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("❗ Misol: <code>/dict apple</code>", parse_mode="HTML")

    word = parts[1].lower().strip()

    if word in dictionary:
        await message.answer(
            f"📖 <b>{word}</b> → <code>{dictionary[word]}</code>\n\n"
            f"📝 <b>Misol:</b>\n_{word.capitalize()}_ — inglizcha so'z",
            parse_mode="HTML"
        )
        return

    matches = [eng for eng, uzb in dictionary.items() if word in uzb.lower()]
    if matches:
        result = "\n".join([f"• <b>{eng}</b> → <code>{dictionary[eng]}</code>" for eng in matches[:5]])
        await message.answer(
            f"📖 <b>'{word}'</b> uchun topildi:\n\n{result}",
            parse_mode="HTML"
        )
    else:
        # Suggest similar words
        similar = [k for k in dictionary.keys() if k.startswith(word[:2])][:3]
        tip = ""
        if similar:
            tip = f"\n\n💡 Shunga o'xshash: {', '.join(similar)}"
        await message.answer(
            f"❌ <b>'{word}'</b> topilmadi.{tip}\n\n"
            f"Inglizcha yoki o'zbekcha yozing.",
            parse_mode="HTML"
        )

@dp.message(F.text == "/random_word")
async def random_word(message: Message):
    word = random.choice(list(dictionary.keys()))
    await message.answer(
        f"🎲 <b>Tasodifiy so'z:</b>\n\n"
        f"📝 <b>{word}</b> → <code>{dictionary[word]}</code>\n\n"
        f"💡 Bu so'zni eslab qoling!",
        parse_mode="HTML"
    )

@dp.message(F.text == "🎲 Random Word")
async def random_word_handler(message: Message):
    word = random.choice(list(dictionary.keys()))
    await message.answer(
        f"🎲 <b>Tasodifiy so'z:</b>\n\n"
        f"📝 <b>{word}</b> → <code>{dictionary[word]}</code>\n\n"
        f"💡 Bu so'zni eslab qoling!\n"
        f"🔄 Yana ko'rish uchun tugmani bosing!",
        parse_mode="HTML"
    )

@dp.message(F.text == "💡 Daily Word")
async def daily_word(message: Message):
    # Seed with today's date for consistent daily word
    today = time.strftime("%Y%m%d")
    random.seed(int(today))
    word = random.choice(list(dictionary.keys()))
    random.seed()  # Reset seed

    await message.answer(
        f"💡 <b>Kunlik so'z — {time.strftime('%d.%m.%Y')}</b>\n\n"
        f"🔤 <b>{word.upper()}</b>\n"
        f"🇺🇿 <code>{dictionary[word]}</code>\n\n"
        f"📖 <b>Misol:</b>\n"
        f"<i>{word.capitalize()} is an important word to know.</i>\n\n"
        f"📌 Bu so'zni bugun 5 marta ishlating!",
        parse_mode="HTML"
    )

# ================= LEADERBOARD =================
@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message):
    cur.execute("SELECT user_id, username, score FROM users ORDER BY score DESC LIMIT 10")
    rows = cur.fetchall()

    if not rows:
        return await message.answer("🏆 Hali hech kim test topshirmagan.")

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>TOP 10 FOYDALANUVCHILAR:</b>\n\n"
    for i, (uid, username, score) in enumerate(rows, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = f"@{username}" if username else f"User {uid}"
        bar = "█" * min(int(score / 10), 10)
        text += f"{medal} {name}\n    💰 {score} ball {bar}\n\n"

    await message.answer(text, parse_mode="HTML")

# ================= MY MISTAKES =================
@dp.message(F.text == "❌ My Mistakes")
async def my_mistakes(message: Message):
    uid = message.from_user.id
    cur.execute(
        "SELECT question, your_answer, correct_answer FROM mistakes "
        "WHERE user_id = ? ORDER BY rowid DESC LIMIT 10",
        (uid,)
    )
    rows = cur.fetchall()

    if not rows:
        return await message.answer("✅ Siz hali xato qilmadingiz! Zo'r!")

    text = "❌ <b>So'nggi 10 ta xatoyingiz:</b>\n\n"
    for i, (q, your, correct) in enumerate(rows, 1):
        q_safe = q.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        text += (
            f"<b>{i}.</b> {q_safe}\n"
            f"   Siz: ❌ <code>{your}</code>\n"
            f"   To'g'ri: ✅ <code>{correct}</code>\n\n"
        )

    await message.answer(text, parse_mode="HTML")

# ================= MY STATS =================
@dp.message(F.text == "📊 My Stats")
@dp.message(F.text == "/stats")
async def my_stats(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    cur.execute("SELECT username, score, total_tests FROM users WHERE user_id = ?", (uid,))
    row = cur.fetchone()
    if not row:
        return await message.answer("Ma'lumot topilmadi.")

    username, score, total_tests = row
    cur.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ?", (uid,))
    mistake_count = cur.fetchone()[0]

    avg = round(score / total_tests, 1) if total_tests > 0 else 0
    cur.execute("SELECT COUNT(*) FROM users WHERE score > ?", (score,))
    rank_above = cur.fetchone()[0] + 1

    await message.answer(
        f"📊 <b>Shaxsiy statistika</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Foydalanuvchi: @{username}\n"
        f"🏆 Umumiy ball: <b>{score}</b>\n"
        f"📝 Testlar soni: <b>{total_tests}</b>\n"
        f"📈 O'rtacha ball: <b>{avg}</b>\n"
        f"❌ Xatolar: <b>{mistake_count}</b>\n"
        f"🥇 Reyting: <b>#{rank_above}</b>\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

# ================= DUEL =================
@dp.message(F.text == "⚔️ Duel")
async def duel_menu(message: Message):
    await message.answer(
        "⚔️ <b>DUEL — Do'stingiz bilan musobaqa!</b>\n\n"
        "Duel boshlash uchun:\n"
        "👉 <code>/duel @username</code>\n\n"
        "Misol: <code>/duel @ali_123</code>\n\n"
        "📌 <b>Muhim:</b> Raqibingiz avval botga <code>/start</code> bosgan bo'lishi kerak!\n\n"
        "📋 <b>Qoidalar:</b>\n"
        "• Raqibga avtomatik tugmali chaqiruv yuboriladi\n"
        "• Ikkovingiz 10 ta bir xil savolga javob berasiz\n"
        "• Har bir savol uchun 15 sekund\n"
        "• Ko'proq ball to'plagan g'olib!\n"
        "• Natija duel tugagandan so'ng e'lon qilinadi\n"
        "• Raqib 5 daqiqa ichida qabul qilmasa — bekor bo'ladi",
        parse_mode="HTML"
    )

@dp.message(F.text.startswith("/duel"))
async def start_duel(message: Message):
    uid = message.from_user.id
    parts = message.text.strip().split()

    if len(parts) < 2:
        return await message.answer("❗ Misol: <code>/duel @username</code>", parse_mode="HTML")

    opponent_username = parts[1].lstrip("@")
    my_username = message.from_user.username or str(uid)
    my_name = message.from_user.full_name or my_username

    if opponent_username.lower() == my_username.lower():
        return await message.answer("❌ O'zingiz bilan duel bo'lmaydi!")

    # Raqibning user_id sini DB dan qidirish
    cur.execute("SELECT user_id FROM users WHERE LOWER(username) = ?", (opponent_username.lower(),))
    row = cur.fetchone()

    if not row:
        return await message.answer(
            f"❌ <b>@{opponent_username}</b> botda ro'yxatdan o'tmagan!\n\n"
            f"💡 Ular avval botga <code>/start</code> bosishlari kerak.",
            parse_mode="HTML"
        )

    opponent_id = row[0]

    # Allaqachon duel kutayotgan bo'lsa
    if uid in [v.get("challenger_id") for v in duel_waiting.values()]:
        return await message.answer("⚠️ Sizning avvalgi duel chaqiruvingiz hali kutilmoqda!")

    # Create duel
    duel_id = f"duel_{uid}_{int(time.time())}"
    selected = random.sample(reading_questions, 10)
    questions_json = str([{"q": q["q"], "options": q["options"], "a": q["a"], "pts": q.get("pts", 1)} for q in selected])

    cur.execute(
        "INSERT INTO duels VALUES (?,?,?,?,?,?,?,?,?)",
        (duel_id, uid, opponent_id, 0, 0, 0, 0, questions_json, "waiting")
    )
    conn.commit()

    # duel_waiting ga saqlash — opponent_id bo'yicha
    duel_waiting[opponent_id] = {
        "duel_id": duel_id,
        "challenger_id": uid,
        "challenger_name": my_name,
        "challenger_username": my_username,
        "questions": selected
    }

    # Chaqiruvchiga xabar
    await message.answer(
        f"⚔️ <b>Duel chaqiruvi yuborildi!</b>\n\n"
        f"📨 @{opponent_username} ga taklif yuborildi.\n"
        f"Ular qabul qilishini kuting...\n\n"
        f"⏳ 5 daqiqa ichida qabul qilmasa, chaqiruv bekor bo'ladi.",
        parse_mode="HTML"
    )

    # Raqibga to'g'ridan tugmali xabar yuborish
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"duel_accept_{duel_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"duel_reject_{duel_id}"),
        ]
    ])
    try:
        await bot.send_message(
            opponent_id,
            f"⚔️ <b>DUEL CHAQIRUVI!</b>\n\n"
            f"👤 <b>{my_name}</b> (@{my_username}) sizni duelga chaqirmoqda!\n\n"
            f"📝 10 ta savol | ⏱ 15 sek/savol\n"
            f"🏆 Ko'proq ball to'plagan g'olib!\n\n"
            f"Qabul qilasizmi?",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"⚠️ @{opponent_username} ga xabar yuborib bo'lmadi.\n"
            f"Ular botni bloklab qo'ygan bo'lishi mumkin."
        )
        duel_waiting.pop(opponent_id, None)
        return

    # 5 daqiqadan keyin avtomatik bekor qilish
    asyncio.create_task(duel_expire(duel_id, uid, opponent_id, 300))


async def duel_expire(duel_id, challenger_id, opponent_id, timeout):
    """5 daqiqa ichida qabul qilinmasa duelni bekor qiladi"""
    await asyncio.sleep(timeout)
    if duel_waiting.get(opponent_id, {}).get("duel_id") == duel_id:
        duel_waiting.pop(opponent_id, None)
        cur.execute("UPDATE duels SET status = 'expired' WHERE duel_id = ?", (duel_id,))
        conn.commit()
        try:
            await bot.send_message(challenger_id, "⏰ Duel chaqiruvi muddati tugadi. Raqib javob bermadi.")
        except:
            pass


@dp.callback_query(F.data.startswith("duel_accept_"))
async def duel_accept_callback(callback: CallbackQuery):
    uid = callback.from_user.id  # raqib (qabul qiluvchi)
    duel_id = callback.data.replace("duel_accept_", "")

    duel_info = duel_waiting.get(uid)
    if not duel_info or duel_info["duel_id"] != duel_id:
        return await callback.answer("❌ Bu chaqiruv endi mavjud emas!", show_alert=True)

    challenger_id = duel_info["challenger_id"]
    challenger_name = duel_info["challenger_name"]
    challenger_username = duel_info["challenger_username"]
    questions = duel_info["questions"]
    accepter_name = callback.from_user.full_name or callback.from_user.username or str(uid)
    accepter_username = callback.from_user.username or str(uid)

    # Tugmani o'chirish
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    cur.execute("UPDATE duels SET status = 'active' WHERE duel_id = ?", (duel_id,))
    conn.commit()

    del duel_waiting[uid]

    # Ikki o'yinchi uchun state yaratish
    for player_uid, opp_uid in [(challenger_id, uid), (uid, challenger_id)]:
        state[player_uid] = {
            "section": "duel",
            "index": 0,
            "questions": questions,
            "score": 0,
            "max_pts": sum(q.get("pts", 1) for q in questions),
            "start_time": time.time(),
            "duel_id": duel_id,
            "opponent_id": opp_uid,
            "correct": 0,
            "wrong": 0,
            "timeouts": 0,
        }

    # Qabul qiluvchiga xabar
    await callback.message.answer(
        f"⚔️ <b>DUEL BOSHLANDI!</b>\n\n"
        f"👤 Raqib: <b>{challenger_name}</b> (@{challenger_username})\n"
        f"📝 10 ta savol | ⏱ 15 sek/savol\n\n"
        f"🥊 Omad!",
        parse_mode="HTML"
    )

    # Chaqiruvchiga xabar
    try:
        await bot.send_message(
            challenger_id,
            f"⚔️ <b>DUEL BOSHLANDI!</b>\n\n"
            f"👤 Raqib: <b>{accepter_name}</b> (@{accepter_username}) qabul qildi!\n"
            f"📝 10 ta savol | ⏱ 15 sek/savol\n\n"
            f"🥊 Omad!",
            parse_mode="HTML"
        )
    except:
        pass

    # Ikki o'yinchiga ham savollarni yuborish
    await send_duel_q(callback.message, uid)
    await send_duel_q_by_id(challenger_id)


@dp.callback_query(F.data.startswith("duel_reject_"))
async def duel_reject_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    duel_id = callback.data.replace("duel_reject_", "")

    duel_info = duel_waiting.get(uid)
    if not duel_info or duel_info["duel_id"] != duel_id:
        return await callback.answer("Bu chaqiruv endi mavjud emas!", show_alert=True)

    challenger_id = duel_info["challenger_id"]
    rejecter_name = callback.from_user.full_name or callback.from_user.username or str(uid)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    duel_waiting.pop(uid, None)
    cur.execute("UPDATE duels SET status = 'rejected' WHERE duel_id = ?", (duel_id,))
    conn.commit()

    await callback.answer("Duel rad etildi.")
    await callback.message.answer("❌ Siz duelni rad etdingiz.")

    try:
        await bot.send_message(
            challenger_id,
            f"😔 <b>{rejecter_name}</b> duelni rad etdi.\n\nBoshqa do'stingizni sinab ko'ring! ⚔️",
            parse_mode="HTML"
        )
    except:
        pass

async def send_duel_q_by_id(uid):
    s = state.get(uid)
    if not s:
        return
    q = s["questions"][s["index"]]
    pts_label = get_pts_label(q.get("pts", 1))
    text = (
        f"⚔️ <b>DUEL — Savol {s['index']+1}/10</b> {pts_label}\n\n"
        f"{q['q']}\n\n"
        + "\n".join(q["options"])
        + "\n\n⏱ <b>15 sekund!</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="dans_A"),
         InlineKeyboardButton(text="B", callback_data="dans_B")],
        [InlineKeyboardButton(text="C", callback_data="dans_C"),
         InlineKeyboardButton(text="D", callback_data="dans_D")],
    ])
    await bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")

    await cancel_timer(uid)
    task = asyncio.create_task(duel_timer(uid, 15))
    timer_tasks[uid] = task

async def send_duel_q(message: Message, uid):
    s = state.get(uid)
    if not s:
        return
    q = s["questions"][s["index"]]
    pts_label = get_pts_label(q.get("pts", 1))
    text = (
        f"⚔️ <b>DUEL — Savol {s['index']+1}/10</b> {pts_label}\n\n"
        f"{q['q']}\n\n"
        + "\n".join(q["options"])
        + "\n\n⏱ <b>15 sekund!</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="dans_A"),
         InlineKeyboardButton(text="B", callback_data="dans_B")],
        [InlineKeyboardButton(text="C", callback_data="dans_C"),
         InlineKeyboardButton(text="D", callback_data="dans_D")],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

    await cancel_timer(uid)
    task = asyncio.create_task(duel_timer(uid, 15))
    timer_tasks[uid] = task

async def duel_timer(uid, timeout):
    await asyncio.sleep(timeout)
    s = state.get(uid)
    if not s or s.get("section") != "duel":
        return

    q = s["questions"][s["index"]]
    s["index"] += 1
    s["timeouts"] = s.get("timeouts", 0) + 1

    correct_option = next((opt for opt in q['options'] if opt.startswith(q['a'] + ')')), q['a'])
    await bot.send_message(uid, f"⏰ <b>Vaqt tugadi!</b>\n✅ To'g'ri javob: <b>{correct_option}</b>", parse_mode="HTML")

    if s["index"] < len(s["questions"]):
        await asyncio.sleep(1)
        await send_duel_q_by_id(uid)
    else:
        await finish_duel(uid)

@dp.callback_query(F.data.startswith("dans_"))
async def duel_answer(callback: CallbackQuery):
    uid = callback.from_user.id
    s = state.get(uid)

    if not s or s.get("section") != "duel":
        return await callback.answer("Duel topilmadi!", show_alert=True)

    await cancel_timer(uid)
    chosen = callback.data.split("_")[1]
    q = s["questions"][s["index"]]
    pts = q.get("pts", 1)
    correct_option = next((opt for opt in q["options"] if opt.startswith(q["a"] + ")")), q["a"])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    if chosen == q["a"]:
        s["score"] += pts
        s["correct"] += 1
        await callback.answer("✅ To'g'ri!")
        await callback.message.answer(
            f"✅ <b>To'g'ri!</b> +{pts} ball\n📌 <b>{correct_option}</b>",
            parse_mode="HTML"
        )
    else:
        s["wrong"] += 1
        await callback.answer("❌ Noto'g'ri!")
        await callback.message.answer(
            f"❌ <b>Noto'g'ri!</b>\nSiz: <b>{chosen}</b> | ✅ To'g'ri: <b>{correct_option}</b>",
            parse_mode="HTML"
        )

    s["index"] += 1
    if s["index"] < len(s["questions"]):
        await send_duel_q(callback.message, uid)
    else:
        await finish_duel(uid)

async def finish_duel(uid):
    await cancel_timer(uid)
    s = state.get(uid)
    if not s:
        return

    duel_id = s.get("duel_id")
    opponent_id = s.get("opponent_id")
    score = s["score"]

    # Save my score
    cur.execute("SELECT player1, player2, p1_score, p2_score, p1_done, p2_done FROM duels WHERE duel_id = ?", (duel_id,))
    row = cur.fetchone()
    if not row:
        state.pop(uid, None)
        return

    p1, p2, p1s, p2s, p1d, p2d = row

    if uid == p1:
        cur.execute("UPDATE duels SET p1_score = ?, p1_done = 1 WHERE duel_id = ?", (score, duel_id))
    else:
        cur.execute("UPDATE duels SET p2_score = ?, p2_done = 1 WHERE duel_id = ?", (score, duel_id))
    conn.commit()

    await bot.send_message(
        uid,
        f"✅ <b>Duel qisminiz tugadi!</b>\n"
        f"🏆 Sizning ballingiz: <b>{score}</b>\n\n"
        f"⏳ Raqib kutilmoqda...",
        parse_mode="HTML"
    )

    # Check if both done
    cur.execute("SELECT p1_score, p2_score, p1_done, p2_done FROM duels WHERE duel_id = ?", (duel_id,))
    row2 = cur.fetchone()
    if row2 and row2[2] == 1 and row2[3] == 1:
        p1_score, p2_score = row2[0], row2[1]
        cur.execute("UPDATE duels SET status = 'done' WHERE duel_id = ?", (duel_id,))
        conn.commit()

        # Announce winner
        if p1_score > p2_score:
            winner_id, loser_id = p1, p2
            w_score, l_score = p1_score, p2_score
        elif p2_score > p1_score:
            winner_id, loser_id = p2, p1
            w_score, l_score = p2_score, p1_score
        else:
            # Draw
            for pid in [p1, p2]:
                try:
                    await bot.send_message(pid, "🤝 <b>Duel — Durang!</b>\nIkkovingiz teng ball to'pladingiz!", parse_mode="HTML")
                except:
                    pass
            for pid in [p1, p2]:
                state.pop(pid, None)
            return

        # Update winner score
        cur.execute("UPDATE users SET score = score + ? WHERE user_id = ?", (w_score, winner_id))
        conn.commit()

        try:
            await bot.send_message(
                winner_id,
                f"🏆 <b>DUEL G'OLIBI SIZMISIZ!</b>\n\n"
                f"✅ Sizning ball: <b>{w_score}</b>\n"
                f"❌ Raqib ball: <b>{l_score}</b>\n\n"
                f"🎉 Tabriklaymiz! +{w_score} ball qo'shildi!",
                parse_mode="HTML"
            )
        except:
            pass

        try:
            await bot.send_message(
                loser_id,
                f"😔 <b>Duelda yutqazdingiz...</b>\n\n"
                f"✅ Sizning ball: <b>{l_score}</b>\n"
                f"🏆 Raqib ball: <b>{w_score}</b>\n\n"
                f"💪 Ko'proq mashq qiling va qayta sinab ko'ring!",
                parse_mode="HTML"
            )
        except:
            pass

    state.pop(uid, None)

# ================= WORD GAME =================
@dp.message(F.text == "🎮 Word Game")
async def word_game(message: Message):
    uid = message.from_user.id
    word_data = random.choice(word_game_words)
    word = word_data["word"]
    hint = word_data["hint"]

    # Scramble the word
    letters = list(word)
    random.shuffle(letters)
    scrambled = " ".join(letters)

    state[f"game_{uid}"] = {
        "word": word,
        "hint": hint,
        "scrambled": scrambled,
        "attempts": 0,
        "start_time": time.time()
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Ko'proq maslahat", callback_data=f"game_hint_{uid}"),
         InlineKeyboardButton(text="⏭️ O'tkazib yuborish", callback_data=f"game_skip_{uid}")]
    ])

    await message.answer(
        f"🎮 <b>SO'Z TOPISH O'YINI</b>\n\n"
        f"🔀 Aralashtirilgan harf: <code>{scrambled}</code>\n\n"
        f"💡 Maslahat: {hint}\n\n"
        f"✏️ Javobingizni yozing:",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def check_word_game(message: Message, uid, game):
    answer = message.text.strip().upper()
    correct = game["word"]
    game["attempts"] += 1

    if answer == correct:
        elapsed = round(time.time() - game["start_time"])
        pts = max(10 - game["attempts"] + 1, 1) * (1 if elapsed > 30 else 2)

        ensure_user(uid)
        cur.execute("UPDATE users SET score = score + ? WHERE user_id = ?", (pts, uid))
        conn.commit()

        await message.answer(
            f"🎉 <b>TO'G'RI!</b>\n\n"
            f"✅ So'z: <b>{correct}</b>\n"
            f"🏆 +{pts} ball qo'shildi!\n"
            f"🔢 Urinishlar soni: {game['attempts']}\n"
            f"⏱ Vaqt: {elapsed} sek\n\n"
            f"🎮 Yangi o'yin uchun '🎮 Word Game' ni bosing!",
            parse_mode="HTML"
        )
        state.pop(f"game_{uid}", None)
    else:
        remaining = max(3 - game["attempts"], 0)
        if game["attempts"] >= 3:
            await message.answer(
                f"❌ <b>Urinishlar tugadi!</b>\n\n"
                f"To'g'ri so'z: <b>{correct}</b>\n\n"
                f"💪 Qayta urinib ko'ring!",
                parse_mode="HTML"
            )
            state.pop(f"game_{uid}", None)
        else:
            await message.answer(
                f"❌ Noto'g'ri! Qaytadan urining.\n"
                f"🔀 <code>{game['scrambled']}</code>\n"
                f"💡 {game['hint']}\n"
                f"🔢 Qolgan urinishlar: <b>{remaining}</b>",
                parse_mode="HTML"
            )

@dp.callback_query(F.data.startswith("game_hint_"))
async def game_hint(callback: CallbackQuery):
    uid = callback.from_user.id
    game = state.get(f"game_{uid}")
    if not game:
        return await callback.answer("O'yin topilmadi!", show_alert=True)

    word = game["word"]
    revealed = word[0] + "_" * (len(word) - 2) + word[-1]
    await callback.answer(f"💡 Birinchi va oxirgi harf: {revealed}", show_alert=True)

@dp.callback_query(F.data.startswith("game_skip_"))
async def game_skip(callback: CallbackQuery):
    uid = callback.from_user.id
    game = state.get(f"game_{uid}")
    if not game:
        return await callback.answer("O'yin topilmadi!", show_alert=True)

    word = game["word"]
    state.pop(f"game_{uid}", None)
    await callback.message.answer(
        f"⏭️ <b>O'tkazib yuborildi!</b>\n\n"
        f"To'g'ri so'z: <b>{word}</b>\n\n"
        f"🎮 Yangi o'yin uchun '🎮 Word Game' ni bosing!",
        parse_mode="HTML"
    )

# ================= RUN =================
async def main():
    print("🤖 IELTS Bot ishga tushdi...")
    print("✅ Barcha funksiyalar faol:")
    print("   📚 Reading (15 sek taymer, ball tizimi)")
    print("   ✍️ Writing (avtomatik baholash)")
    print("   ⚔️ Duel (ikki o'yinchi)")
    print("   🎮 Word Game (so'z topish)")
    print("   📖 Dictionary + Daily Word")
    print("   📊 Stats + Leaderboard")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
