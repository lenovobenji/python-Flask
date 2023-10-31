from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column

from dogtor.db import db 

class User(db.Model):
    id = mapped_column(Integer, primary_key=True)
    first_name = db.Column(String(length=50), nullable=False)
    last_name = db.Column(String(length=50), nullable=True)
    email = db.Column(String, unique=True, nullable=False)
    password = db.Column(String, nullable=False)


class Owner(db.Model):
    """Pet owner object"""

    id = db.Column(Integer, primary_key=True)
    first_name = db.Column(String(length=50))
    last_name = db.Column(String(length=50))
    phone = db.Column(String(length=15))
    mobile = db.Column(String(length=15))
    email = db.Column(String, unique=True)
    pets = db.relationship("Pet", back_populates="owner")

    def to_dict(self):
        """Owner dictionary representation"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "pets": [pet.to_dict() for pet in self.pets],
        }


class Species(db.Model):
    """Pet species object"""

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(length=20), unique=True)
    pets = db.relationship("Pet", back_populates="species")

    def to_dict(self):
        """Species dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
        }


class Pet(db.Model):
    """Pet object"""

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(length=20))
    owner_id = db.Column(Integer, db.ForeignKey("owner.id"))
    age = db.Column(Integer)
    species_id = db.Column(Integer, db.ForeignKey("species.id"))

    species = db.relationship("Species", back_populates="pets")
    owner = db.relationship("Owner", back_populates="pets")
    records = db.relationship("Record", back_populates="pet")

    def to_dict(self):
        """Pet dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "age": self.age,
            "species": self.species.name,
            # "records": [record.to_dict() for record in self.records],
        }


record_category_m2m = db.Table(
    "record_category",
    db.Column("record_id", Integer, db.ForeignKey("record.id")),
    db.Column("category_id", Integer, db.ForeignKey("category.id")),
)


class Record(db.Model):
    """Pet record object"""

    id = db.Column(Integer, primary_key=True)
    procedure = db.Column(String(length=255))
    date = db.Column(DateTime)
    pet_id = db.Column(Integer, db.ForeignKey("pet.id"))
    pet = db.relationship("Pet", back_populates="records")
    categories = db.relationship(
        "Category", secondary=record_category_m2m, back_populates="records"
    )


class Category(db.Model):
    """Record category object"""

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(length=20))
    records = db.relationship(
        "Record", secondary=record_category_m2m, back_populates="categories"
    )
