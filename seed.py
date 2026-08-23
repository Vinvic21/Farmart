from faker import Faker
from app import app
from extensions import db
from models import User, Profile, Animal

fake = Faker()

ANIMAL_TYPES = {
    "Cow": ["Friesian", "Jersey", "Ayrshire", "Guernsey"],
    "Goat": ["Boer", "Kalahari Red", "Saanen", "Toggenburg"],
    "Sheep": ["Dorper", "Merino", "Romney", "Suffolk"],
    "Chicken": ["Kienyeji", "Broiler", "Layer", "Rhode Island Red"],
    "Pig": ["Landrace", "Large White", "Duroc"],
}

NUM_FARMERS = 8
NUM_BUYERS = 12
ANIMALS_PER_FARMER = 5


def create_user(role):
    user = User(
        email=fake.unique.email(),
        role=role,
    )
    user.set_password("password123")  # fixed test password for all seeded users
    db.session.add(user)
    db.session.flush()  # get user.id before commit, so Profile can reference it

    profile = Profile(
        user_id=user.id,
        phone=fake.phone_number(),
        location=fake.city(),
        verification_status=fake.random_element(["pending", "verified"]),
    )
    db.session.add(profile)

    return user


def create_animal(farmer):
    animal_type = fake.random_element(list(ANIMAL_TYPES.keys()))
    breed = fake.random_element(ANIMAL_TYPES[animal_type])

    animal = Animal(
        farmer_id=farmer.id,
        type=animal_type,
        breed=breed,
        age=fake.random_int(min=1, max=10),
        price=round(fake.random_number(digits=4) + fake.random.random(), 2),
        status=fake.random_element(["available", "available", "available", "sold"]),  # weighted toward available
        description=fake.sentence(nb_words=12),
    )
    db.session.add(animal)


def seed():
    print("Clearing existing data...")
    db.session.query(Animal).delete()
    db.session.query(Profile).delete()
    db.session.query(User).delete()
    db.session.commit()

    print(f"Creating {NUM_FARMERS} farmers...")
    farmers = [create_user("farmer") for _ in range(NUM_FARMERS)]
    db.session.commit()

    print(f"Creating {NUM_BUYERS} buyers...")
    buyers = [create_user("buyer") for _ in range(NUM_BUYERS)]
    db.session.commit()

    print(f"Creating animals for each farmer...")
    for farmer in farmers:
        for _ in range(ANIMALS_PER_FARMER):
            create_animal(farmer)
    db.session.commit()

    print("Seeding complete.")
    print(f"  Farmers: {len(farmers)}")
    print(f"  Buyers: {len(buyers)}")
    print(f"  Animals: {NUM_FARMERS * ANIMALS_PER_FARMER}")


if __name__ == "__main__":
    with app.app_context():
        seed()