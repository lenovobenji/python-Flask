from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import request
from werkzeug.security import check_password_hash, generate_password_hash

from dogtor.config import Config
from dogtor.db import db

from . import api, models


def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        prefix = "Bearer "

        if not authorization:
            return {"detail": 'Missing "Authorization" header'}, 401

        if not authorization.startswith(prefix):
            return {"detail": "Invalid token prefix"}, 401

        token = authorization.split(" ")[1]
        if not token:
            return {"detail": "Missing token"}, 401

        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        except jwt.exceptions.ExpiredSignatureError:
            return {"detail": "Token expired"}, 401
        except jwt.exceptions.InvalidTokenError:
            return {"detail": "Invalid token"}, 401

        request.user = db.session.execute(
            db.select(models.User).where(models.User.id == payload["sub"])
        ).scalar_one()

        return func(*args, **kwargs)

    return wrapper


@api.route("/profile/", methods=["POST"])
@token_required
def profile():
    """Returns current user details"""
    user = request.user
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }


@api.route("/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
@api.route("/users/", methods=["GET", "POST"])
def users(user_id=None):
    if user_id is not None:
        found_user = None
        for user in users:
            if user["id"] == user_id:
                found_user = user

        if request.method == "PUT":
            return {"detail": f"user {found_user['username']} modified"}
        if request.method == "DELETE":
            return {"detail": f"user {found_user['username']} deleted"}

        return found_user

    if request.method == "POST":
        data = request.data
        return {"detail": f"user {data['username']} created"}
    return users


@api.get("/pets/")
@token_required
def get_pets():
    """Returns all pets"""
    query = db.select(models.Pet)
    pets = db.session.execute(query).scalars()
    return [pet.to_dict() for pet in pets]


@api.get("/pets/<int:pet_id>")
@token_required
def get_pet(pet_id):
    """Returns a Pet"""
    query = db.select(models.Pet).where(models.Pet.id == pet_id)
    pet = db.session.execute(query).scalar()

    if pet is None:
        return {"detail": "Pet not found"}, 404

    return pet.to_dict()


@api.post("/pets/")
@token_required
def create_pet():
    """Creates a new pet"""
    data = request.get_json()
    required_fields = ["name", "owner_id", "age", "species_id"]
    for field in required_fields:
        if field not in data:
            return {"detail": f'"{field}" field is required'}, 400

    pet_name = data["name"]
    owner_id = data["owner_id"]
    species_id = data["species_id"]
    query = db.select(models.Pet).where(
        db.func.lower(models.Pet.name) == db.func.lower(pet_name),
        models.Pet.owner_id == owner_id,
        models.Pet.species_id == species_id,
    )
    if db.session.execute(query).scalar() is not None:
        return {"detail": f'Pet "{pet_name}" already exists'}, 409

    pet = models.Pet(
        name=pet_name,
        owner_id=owner_id,
        age=data["age"],
        species_id=species_id,
    )
    db.session.add(pet)
    db.session.commit()
    return pet.to_dict(), 201


@api.put("/pets/<int:pet_id>")
@token_required
def update_pet(pet_id):
    """Updates an existing pet"""
    data = request.get_json()
    query = db.select(models.Pet).where(models.Pet.id == pet_id)
    pet = db.session.execute(query).scalar()
    if pet is None:
        return {"detail": f"Pet with id {pet_id} not found"}, 404

    required_fields = ["name", "owner_id", "age", "species_id"]
    for field in required_fields:
        if field not in data:
            return {"detail": f'"{field}" field is required'}, 400

    for key, value in data.items():
        setattr(pet, key, value)

    db.session.commit()
    return pet.to_dict()


@api.delete("/pets/<int:pet_id>")
@token_required
def delete_pet(pet_id):
    """Deletes an existing pet"""
    query = db.select(models.Pet).where(models.Pet.id == pet_id)
    pet = db.session.execute(query).scalar()
    if pet is None:
        return {"detail": f"pet with id {pet_id} not found"}, 404

    db.session.delete(pet)
    db.session.commit()
    return {"detail": f"pet with id {pet_id} deleted"}, 200


@api.get("/owners/")
@token_required
def get_owners():
    """Returns all pet owners"""
    query = db.select(models.Owner)
    owners = db.session.execute(query).scalars()
    return [owner.to_dict() for owner in owners]


@api.get("/owners/<int:owner_id>")
@token_required
def get_owner(owner_id):
    """Returns a pet owner by id"""
    query = db.select(models.Owner).where(owner_id == models.Owner.id)
    owner = db.session.execute(query).scalar()

    if owner is None:
        return {"detail": "Owner not found"}, 404

    return owner.to_dict()


@api.post("/owners/")
@token_required
def create_owner():
    """Creates a new pet owner"""
    data = request.get_json()
    required_fields = ["first_name", "last_name", "phone", "mobile", "email"]
    for attr in required_fields:
        if attr not in data:
            return {"detail": f'"{attr}" field is required'}, 400

    query = db.select(models.Owner).where(
        db.func.lower(models.Owner.email) == db.func.lower(data["email"])
    )
    if db.session.execute(query).scalar() is not None:
        return {"detail": f"owner with email {data['email']} already exists"}, 409

    owner = models.Owner(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        mobile=data["mobile"],
        email=data["email"],
    )
    db.session.add(owner)
    db.session.commit()
    return owner.to_dict(), 201


@api.put("/owners/<int:owner_id>/")
@token_required
def update_owner(owner_id):
    """Updates an existing pet owner"""
    data = request.get_json()
    query = db.select(models.Owner).where(models.Owner.id == owner_id)
    owner = db.session.execute(query).scalar()
    if owner is None:
        return {"detail": f"owner with id {owner_id} does not exist"}, 404

    required_fields = ["first_name", "last_name", "phone", "mobile", "email"]
    for attr in required_fields:
        if attr not in data:
            return {"detail": f'"{attr}" field is required'}, 400

    for key, value in data.items():
        setattr(owner, key, value)

    db.session.commit()
    return owner.to_dict()


@api.delete("/owners/<int:owner_id>/")
@token_required
def delete_owner(owner_id):
    """Deletes an existing pet owner"""
    query = db.select(models.Owner).where(models.Owner.id == owner_id)
    owner = db.session.execute(query).scalar()
    if owner is None:
        return {"detail": f"owner with id {owner_id} does not exist"}, 404

    db.session.delete(owner)
    db.session.commit()
    return {"detail": f"owner with id {owner_id} deleted successfully"}, 200


@api.route("/procedures/")
def procedures():
    return []


@api.get("/species/")
@token_required
def get_all_species():
    """Returns all pet species"""
    query = db.select(models.Species)
    result = db.session.execute(query).scalars()

    return [species.to_dict() for species in result]


@api.get("/species/<int:species_id>")
@token_required
def get_one_species(species_id):
    """Returns a single species"""
    query = db.select(models.Species).where(models.Species.id == species_id)
    species = db.session.execute(query).scalar()
    if species is None:
        return {"detail": "Species not found"}, 404
    return species.to_dict()


@api.post("/species/")
@token_required
def create_species():
    """Create a new pet species"""
    data = request.get_json()
    if "name" not in data:
        return {"detail": 'Field "name" is required'}, 400

    query = db.select(models.Species).where(
        db.func.lower(models.Species.name) == db.func.lower(data["name"])
    )
    if db.session.execute(query).scalar():
        return {"detail": "Species already exists"}, 409

    species = models.Species(name=data["name"])
    db.session.add(species)
    db.session.commit()

    return species.to_dict(), 201


@api.put("/species/<int:species_id>")
@token_required
def update_species(species_id):
    """Update a pet species"""
    data = request.get_json()
    if "name" not in data:
        return {"detail": 'Field "name" is required'}, 400

    species = db.session.execute(
        db.select(models.Species).where(models.Species.id == species_id)
    ).scalar()
    species.name = data["name"]
    db.session.commit()

    return species.to_dict()


@api.delete("/species/<int:species_id>")
@token_required
def delete_species(species_id):
    """Delete a pet species"""
    species = db.session.execute(
        db.select(models.Species).where(models.Species.id == species_id)
    ).scalar()
    if not species:
        return {"detail": "Species not found"}, 404

    db.session.delete(species)
    db.session.commit()

    return {"detail": "Species deleted"}, 200


@api.route("/signup/", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return {"detail": "email is required"}, 400

    user_exists = db.session.execute(
        db.select(models.User).where(models.User.email == email)
    ).scalar_one_or_none()

    if user_exists:
        return {"detail": "email already taken"}, 400

    password = data.get("password")

    user = models.User(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=email,
        password=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return {"detail": "user created successfully"}, 201


@api.route("/login/", methods=["POST"])
def login():
    """Login an app user"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"detail": "missing email or password"}, 400

    user = db.session.execute(
        db.select(models.User).where(models.User.email == email)
    ).scalar_one_or_none()

    if not user or not check_password_hash(user.password, password):
        return {"detail": "invalid email or password"}, 401

    token = jwt.encode(
        {
            "sub": user.id,
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        Config.SECRET_KEY,
    )

    return {"token": token}
