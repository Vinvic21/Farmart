import random
from faker import Faker
from app import app
from extensions import db
from models import User, Profile, Animal, Cart, CartItem, Order, OrderItem, Payment

fake = Faker()

# Kenyan first/last names, spanning several communities (Kikuyu, Luo,
# Luhya, Kamba, Kalenjin, coastal/Swahili) so seeded farmers/buyers feel
# authentic rather than generic Faker defaults.
KENYAN_MALE_FIRST_NAMES = [
    "Kevin", "Brian", "James", "John", "Peter", "David", "Samuel", "Daniel",
    "Kamau", "Mwangi", "Njoroge", "Kariuki", "Otieno", "Omondi", "Odhiambo",
    "Wafula", "Wanyama", "Simiyu", "Kiptoo", "Kiprop", "Kipchoge", "Kipketer",
    "Mutua", "Musyoka", "Kilonzo", "Hassan", "Omar", "Abdullahi", "Juma",
    "Erick", "Dennis", "Collins", "Felix", "Victor", "Elvis", "Moses",
    "Joseph", "Stephen", "Patrick", "Anthony", "Charles", "Francis",
]
KENYAN_FEMALE_FIRST_NAMES = [
    "Mary", "Grace", "Faith", "Joyce", "Ann", "Jane", "Lucy", "Esther",
    "Wanjiru", "Njeri", "Wambui", "Nyokabi", "Achieng", "Adhiambo", "Akinyi",
    "Nafula", "Nekesa", "Chebet", "Chepkoech", "Jepkosgei", "Cherono",
    "Mueni", "Wavinya", "Ndunge", "Amina", "Fatuma", "Halima", "Zainab",
    "Sharon", "Nancy", "Purity", "Caroline", "Diana", "Irene", "Winnie",
    "Beatrice", "Catherine", "Agnes", "Eunice", "Priscilla", "Consolata",
]
KENYAN_SURNAMES = [
    "Kamau", "Mwangi", "Njoroge", "Kariuki", "Maina", "Ndungu", "Gitau",
    "Otieno", "Omondi", "Odhiambo", "Owino", "Ochieng", "Onyango",
    "Wafula", "Wanyama", "Simiyu", "Wekesa", "Barasa", "Situma",
    "Kiptoo", "Kiprop", "Kipchoge", "Kipketer", "Rotich", "Ruto",
    "Mutua", "Musyoka", "Kilonzo", "Mwikali", "Nzioka",
    "Hassan", "Omar", "Abdullahi", "Mohamed", "Ali",
    "Kimani", "Njuguna", "Waweru", "Karanja", "Muthoni",
]
KENYAN_TOWNS = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Nyeri",
    "Machakos", "Meru", "Kakamega", "Kitale", "Malindi", "Naivasha",
    "Kericho", "Kitui", "Embu", "Garissa", "Bungoma", "Nanyuki", "Voi",
]


def kenyan_first_last():
    is_male = random.choice([True, False])
    first = random.choice(KENYAN_MALE_FIRST_NAMES if is_male else KENYAN_FEMALE_FIRST_NAMES)
    last = random.choice(KENYAN_SURNAMES)
    return first, last


def kenyan_phone():
    # Safaricom/Airtel-style Kenyan mobile numbers: 07XX XXX XXX or 01XX XXX XXX
    prefix = random.choice(["070", "071", "072", "074", "079", "011", "010"])
    return f"{prefix}{random.randint(1000000, 9999999)}"


_used_emails = set()


def kenyan_email(first, last):
    slug = f"{first}.{last}".lower()
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])
    email = f"{slug}{random.randint(10, 999)}@{domain}"
    while email in _used_emails:
        email = f"{slug}{random.randint(10, 999)}@{domain}"
    _used_emails.add(email)
    return email


ANIMAL_PROFILES = [
   
    {
        "type": "Cow",
        "breed": "Holstein Friesian",
        "age": 30,
        "price": 180000,
        "description": "Black-and-white pedigree dairy cow, the world's highest-yielding "
                        "breed, producing 20-25 litres of milk a day on good feed.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Holstein_friesian_or_friesian_cow.jpg",
    },
    {
        "type": "Cow",
        "breed": "Jersey",
        "age": 34,
        "price": 120000,
        "description": "Compact, fawn-coloured dairy cow prized for milk with "
                        "exceptionally high butterfat content, ideal for a small zero-grazing unit.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Jersey_cow,_close-up.jpg",
    },
    {
        "type": "Cow",
        "breed": "Boran",
        "age": 24,
        "price": 110000,
        "description": "Indigenous Kenyan zebu beef breed, heat- and tick-resistant, "
                        "known for fast weight gain and docile temperament on rangeland.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Boran_bull_at_kasarani.jpg",
    },
    {
        "type": "Cow",
        "breed": "Ayrshire",
        "age": 30,
        "price": 140000,
        "description": "Hardy red-and-white Scottish dairy breed that adapts well to "
                        "highland grazing and produces well-balanced milk yields.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/A_cow_on_a_misty_meadow_at_Viikki_(6904473304).jpg",
    },
    {
        "type": "Cow",
        "breed": "Guernsey",
        "age": 32,
        "price": 130000,
        "description": "Golden-brown dairy cow yielding rich, deep-yellow milk high in "
                        "beta-carotene; calmer and lighter-framed than a Holstein.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Guernsey_cattle.jpg",
    },
    
    {
        "type": "Goat",
        "breed": "Boer Goat",
        "age": 12,
        "price": 35000,
        "description": "South African meat goat with a white body and reddish-brown "
                        "head, valued for fast growth and heavy muscling.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Boer_goat444.jpg",
    },
    {
        "type": "Goat",
        "breed": "Anglo-Nubian",
        "age": 14,
        "price": 22000,
        "description": "Large lop-eared dairy goat with a convex Roman nose, giving "
                        "rich, high-butterfat milk and tolerating heat well.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Nubian_goat.jpg",
    },
    {
        "type": "Goat",
        "breed": "Saanen",
        "age": 12,
        "price": 25000,
        "description": "All-white Swiss dairy goat and one of the heaviest milkers "
                        "of any breed, with a calm, easy-to-handle temperament.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Saanen_goat_standing.jpg",
    },
    {
        "type": "Goat",
        "breed": "Toggenburg",
        "age": 12,
        "price": 20000,
        "description": "Swiss dairy goat with a distinctive brown coat and white "
                        "facial stripes, a steady milker on modest feed.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Toggenburger_Goat.jpg",
    },
    {
        "type": "Goat",
        "breed": "Galla Goat",
        "age": 10,
        "price": 12000,
        "description": "Hardy indigenous East African meat goat, drought-tolerant "
                        "and well suited to Kenya's arid and semi-arid rangeland.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/A_Somali_goat_with_a_cruciform_branding.jpg",
    },
    {
        "type": "Sheep",
        "breed": "Dorper",
        "age": 8,
        "price": 15000,
        "description": "South African hair sheep (no shearing needed) bred for "
                        "meat, prized for fast growth and hardiness in dry conditions.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Dorper_white_ram.jpg",
    },
    {
        "type": "Sheep",
        "breed": "Merino",
        "age": 18,
        "price": 12000,
        "description": "World-renowned wool breed producing exceptionally fine, "
                        "soft fleece; also a reliable source of lean meat.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Poll_Merino.jpg",
    },
    {
        "type": "Sheep",
        "breed": "Suffolk",
        "age": 10,
        "price": 14000,
        "description": "Black-faced, black-legged sheep known for rapid growth and "
                        "lean, well-muscled carcasses; a popular terminal meat sire.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Suffolk_Ram_(44505796034).jpg",
    },
    {
        "type": "Sheep",
        "breed": "Romney",
        "age": 16,
        "price": 11000,
        "description": "Dual-purpose English breed with a dense, lustrous fleece "
                        "and a calm nature, doing well on lowland pasture.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Romney_Ewe_and_Lamb.jpg",
    },
    {
        "type": "Chicken",
        "breed": "Rhode Island Red",
        "age": 8,
        "price": 900,
        "description": "Dependable dual-purpose chicken with deep red-brown "
                        "plumage, a steady layer of large brown eggs.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Rhode_Island_Red_Rooster.JPG",
    },
    {
        "type": "Chicken",
        "breed": "Leghorn",
        "age": 6,
        "price": 650,
        "description": "Slim white egg-laying breed famed for high production of "
                        "white eggs on relatively little feed.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/ARS-White_Leghorn_hen.jpg",
    },
    {
        "type": "Chicken",
        "breed": "Buff Orpington",
        "age": 8,
        "price": 1200,
        "description": "Fluffy golden dual-purpose chicken with a docile nature, "
                        "valued for both meat and steady brown-egg laying.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Buff_Orpington.JPG",
    },
    {
        "type": "Chicken",
        "breed": "Plymouth Rock",
        "age": 7,
        "price": 1000,
        "description": "Sturdy black-and-white barred dual-purpose chicken, cold "
                        "hardy and a reliable brown-egg layer.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Barred_Plymouth_Rock_Rooster_2.jpg",
    },
    {
        "type": "Chicken",
        "breed": "Wyandotte",
        "age": 8,
        "price": 1100,
        "description": "Broad-bodied dual-purpose chicken with distinctive laced "
                        "plumage, a good winter layer and calm around people.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Golden_Laced_Wyandotte_Rooster.jpg",
    },
    {
        "type": "Pig",
        "breed": "Large White",
        "age": 6,
        "price": 18000,
        "description": "All-white pig with erect ears and a long body, a strong "
                        "mother with fast growth on commercial feed.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Pig_8907.JPG",
    },
    {
        "type": "Pig",
        "breed": "Duroc",
        "age": 6,
        "price": 22000,
        "description": "Reddish-brown pig with drooping ears, known for lean meat "
                        "yield, fast growth and hardiness outdoors.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Duroc-Schwein.JPG",
    },
    {
        "type": "Pig",
        "breed": "Hampshire",
        "age": 7,
        "price": 20000,
        "description": "Black pig with a distinctive white belt across the "
                        "shoulders and front legs, muscular with lean carcasses.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Champion_Hampshire_Boar_(44211431495).jpg",
    },
    {
        "type": "Pig",
        "breed": "Landrace",
        "age": 6,
        "price": 19000,
        "description": "Long-bodied white pig with heavy lop ears, valued as a "
                        "prolific, milky sow in crossbreeding programmes.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/American_Landrace_Boar.jpg",
    },
    {
        "type": "Pig",
        "breed": "Berkshire",
        "age": 8,
        "price": 24000,
        "description": "Black pig with white points on the face, feet and tail, "
                        "prized for well-marbled, flavourful pork.",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Adelaide_champion_Berkshire_boar_2005.jpg",
    },
]

NUM_FARMERS = 18
NUM_BUYERS = 25
TOTAL_ANIMALS = 204

# Fixed admin account. Not created through /auth/register (which only
# allows farmer/buyer) — this is the one and only way an admin gets into
# the system for now, so keep these credentials in sync with anything you
# tell teammates/graders to log in with.
ADMIN_EMAIL = "farmart@gmail.com"
ADMIN_PASSWORD = "Farmart123"


def create_user(role):
    first, last = kenyan_first_last()
    user = User(
        email=kenyan_email(first, last),
        role=role,
    )
    user.set_password("password123")  # fixed test password for all seeded users
    db.session.add(user)
    db.session.flush()  # get user.id before commit, so Profile can reference it

    profile = Profile(
        user_id=user.id,
        first_name=first,
        last_name=last,
        phone=kenyan_phone(),
        location=random.choice(KENYAN_TOWNS),
        verification_status=fake.random_element(["pending", "verified"]),
    )
    db.session.add(profile)

    return user


def create_admin():
    
    admin = User(
        email=ADMIN_EMAIL,
        role="admin",
    )
    admin.set_password(ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.flush()

    profile = Profile(
        user_id=admin.id,
        first_name="Farmart",
        last_name="Admin",
        phone=kenyan_phone(),
        location="Nairobi",
        verification_status="verified",
    )
    db.session.add(profile)

    return admin


def create_animal(farmer, profile):
    # Small jitter on age/price so repeated uses of the same breed profile
    # (needed to reach 204 animals from 24 hand-authored profiles) don't
    # look like exact duplicates of each other.
    age_jitter = random.randint(-3, 4)
    price_jitter = random.uniform(0.9, 1.12)

    animal = Animal(
        farmer_id=farmer.id,
        type=profile["type"],
        breed=profile["breed"],
        age=max(1, profile["age"] + age_jitter),
        price=round(profile["price"] * price_jitter, -2),  # round to nearest 100
        status=fake.random_element(["available", "available", "available", "sold"]),  # weighted toward available
        description=profile["description"],
        image_url=profile["image_url"],
    )
    db.session.add(animal)


def seed():
    print("Clearing existing data...")
    _used_emails.clear()
    # Delete children before parents to respect FK constraints.
    # Order: cart_items -> carts, payments -> order_items -> orders, then animals -> profiles -> users
    db.session.query(CartItem).delete()
    db.session.query(Cart).delete()
    db.session.query(Payment).delete()
    db.session.query(OrderItem).delete()
    db.session.query(Order).delete()
    db.session.query(Animal).delete()
    db.session.query(Profile).delete()
    db.session.query(User).delete()
    db.session.commit()

    print("Creating admin account...")
    admin = create_admin()
    db.session.commit()

    print(f"Creating {NUM_FARMERS} farmers...")
    farmers = [create_user("farmer") for _ in range(NUM_FARMERS)]
    db.session.commit()

    print(f"Creating {NUM_BUYERS} buyers...")
    buyers = [create_user("buyer") for _ in range(NUM_BUYERS)]
    db.session.commit()

    print(f"Creating {TOTAL_ANIMALS} animals across {NUM_FARMERS} farmers...")
    # Cycle through the 24 hand-authored breed profiles (each with a real,
    # working Wikimedia Commons image) as many times as needed to reach
    # TOTAL_ANIMALS, shuffling each full pass so the order isn't
    # predictable, and round-robin the animals across farmers so every
    # farmer ends up with a realistic, slightly uneven inventory size
    # (204 / 18 farmers -> most get 11-12 animals each).
    animal_index = 0
    profiles_cycle = []
    while animal_index < TOTAL_ANIMALS:
        if not profiles_cycle:
            profiles_cycle = ANIMAL_PROFILES.copy()
            random.shuffle(profiles_cycle)
        profile = profiles_cycle.pop()
        farmer = farmers[animal_index % NUM_FARMERS]
        create_animal(farmer, profile)
        animal_index += 1
    db.session.commit()

    print("Seeding complete.")
    print(f"  Admin:   {admin.email} / {ADMIN_PASSWORD}")
    print(f"  Farmers: {len(farmers)}")
    print(f"  Buyers:  {len(buyers)}")
    print(f"  Animals: {TOTAL_ANIMALS}")


if __name__ == "__main__":
    with app.app_context():
        seed()