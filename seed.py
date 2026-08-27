from faker import Faker
from app import app
from extensions import db
from models import User, Profile, Animal, Cart, CartItem, Order, OrderItem, Payment

fake = Faker()

ANIMAL_TYPES = {
    "Cow": ["Friesian", "Jersey", "Ayrshire", "Guernsey"],
    "Goat": ["Boer", "Kalahari Red", "Saanen", "Toggenburg"],
    "Sheep": ["Dorper", "Merino", "Romney", "Suffolk"],
    "Chicken": ["Kienyeji", "Broiler", "Layer", "Rhode Island Red"],
    "Pig": ["Landrace", "Large White", "Duroc"],
}

ANIMAL_IMAGES = {
    "Cow": [
        "https://images.unsplash.com/photo-1546445317-29f4545e9d53?w=800&q=80",
        "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800&q=80",
        "https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=800&q=80",
    ],
    "Goat": [
        "https://images.unsplash.com/photo-1524024973431-2ad916746881?w=800&q=80",
        "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800&q=80",
    ],
    "Sheep": [
        "https://images.unsplash.com/photo-1484557985045-edf25e08da73?w=800&q=80",
        "https://images.unsplash.com/photo-1484557052118-f32bd25b45b5?w=800&q=80",
    ],
    "Chicken": [
        "https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=800&q=80",
        "https://images.unsplash.com/photo-1518492104633-130d0cc84637?w=800&q=80",
    ],
    "Pig": [
        "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800&q=80",
        "https://images.unsplash.com/photo-1516750105099-4b8a83e217b6?w=800&q=80",
    ],
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
        image_url=fake.random_element(ANIMAL_IMAGES[animal_type]),
    )
    db.session.add(animal)


def seed():
    print("Clearing existing data...")
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