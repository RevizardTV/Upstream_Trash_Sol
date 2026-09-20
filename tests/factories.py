# tests/factories.py
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast
import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import scoped_session, sessionmaker

from py_scripts.database import RecyclingEntry, StaffProfile, UserProfile
from py_scripts.main import hash_password

# Registry that will be bound per-test inside conftest.py
TestSession = scoped_session(sessionmaker())

T = TypeVar("T")


class BaseFactory(Generic[T]):
    """Generic wrapper for static analysis and IDE type inference."""

    @classmethod
    def create_instance(cls: Any, **kwargs: Any) -> T:
        """Type-safe helper to instantiate models."""
        return cast(T, cls.create(**kwargs))


# Define typing bases visible only to Pylance/Pyright
if TYPE_CHECKING:
    _BaseMeta = SQLAlchemyModelFactory.Meta

    class AppBaseFactory(SQLAlchemyModelFactory):
        class Meta(_BaseMeta):
            abstract = True
            sqlalchemy_session = TestSession
            sqlalchemy_session_persistence = "commit"

    _ChildMeta = AppBaseFactory.Meta

else:
    _BaseMeta = object

    class AppBaseFactory(SQLAlchemyModelFactory):
        class Meta(_BaseMeta):
            abstract = True
            sqlalchemy_session = TestSession
            sqlalchemy_session_persistence = "commit"

    _ChildMeta = object


class UserProfileFactory(AppBaseFactory, BaseFactory[UserProfile]):
    class Meta(_ChildMeta):
        model = UserProfile

    id = factory.Sequence(lambda n: n + 1)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    phone_number = "9876543210"
    city = "Coimbatore"
    postal_code = "641001"
    premise_type = "house"
    household_size = 2
    profile_complete = True


class StaffProfileFactory(AppBaseFactory, BaseFactory[StaffProfile]):
    class Meta(_ChildMeta):
        model = StaffProfile

    id = factory.Sequence(lambda n: n + 1)
    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    full_name = factory.Faker("name")
    password_hash = factory.LazyFunction(lambda: hash_password("securepassword123"))
    assigned_pincode = "641001"


class RecyclingEntryFactory(AppBaseFactory, BaseFactory[RecyclingEntry]):
    class Meta(_ChildMeta):
        model = RecyclingEntry

    entry_id = factory.Sequence(lambda n: n + 1)
    user = factory.SubFactory(UserProfileFactory)
    waste_category = "Plastic"
    weight_kg = 5.50
    payout_amount = 110.00
    status = "pending"