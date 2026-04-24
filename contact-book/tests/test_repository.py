from __future__ import annotations

import time

from contacts.models import ContactCreate, ContactUpdate
from contacts.repository import (
    create,
    delete,
    get_by_id,
    list_all,
    search_by_name,
    update,
)


def test_create_minimal(db):
    data = ContactCreate(name="Alice")
    contact = create(data)
    assert contact.name == "Alice"
    assert contact.email is None
    assert contact.phone is None
    assert contact.company is None
    assert contact.notes is None


def test_create_full(db):
    data = ContactCreate(
        name="Alice Smith",
        email="alice@example.com",
        phone="555-1234",
        company="Example Inc",
        notes="A note",
    )
    contact = create(data)
    assert contact.name == "Alice Smith"
    assert contact.email == "alice@example.com"
    assert contact.phone == "555-1234"
    assert contact.company == "Example Inc"
    assert contact.notes == "A note"


def test_create_generates_id(db):
    contact = create(ContactCreate(name="Bob"))
    assert contact.id
    assert isinstance(contact.id, str)
    assert len(contact.id) > 0


def test_create_populates_timestamps(db):
    contact = create(ContactCreate(name="Carol"))
    assert contact.created_at
    assert contact.updated_at
    assert isinstance(contact.created_at, str)
    assert isinstance(contact.updated_at, str)


def test_get_by_id_hit(db):
    created = create(ContactCreate(name="Dana", email="dana@example.com"))
    fetched = get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Dana"
    assert fetched.email == "dana@example.com"


def test_get_by_id_miss(db):
    result = get_by_id("nonexistent-id-12345")
    assert result is None


def test_list_all_empty(db):
    result = list_all()
    assert result == []


def test_list_all_ordered_by_name_asc(db):
    create(ContactCreate(name="Zebra"))
    create(ContactCreate(name="Apple"))
    create(ContactCreate(name="Mango"))
    contacts = list_all()
    assert len(contacts) == 3
    assert [c.name for c in contacts] == ["Apple", "Mango", "Zebra"]


def test_update_full(db):
    contact = create(
        ContactCreate(
            name="Eve",
            email="eve@example.com",
            phone="555-0000",
            company="Old Co",
            notes="Old note",
        )
    )
    updated = update(
        contact.id,
        ContactUpdate(
            name="Eve Updated",
            email="eve.new@example.com",
            phone="555-9999",
            company="New Co",
            notes="New note",
        ),
    )
    assert updated is not None
    assert updated.name == "Eve Updated"
    assert updated.email == "eve.new@example.com"
    assert updated.phone == "555-9999"
    assert updated.company == "New Co"
    assert updated.notes == "New note"
    assert updated.id == contact.id


def test_update_partial_leaves_others_unchanged(db):
    contact = create(
        ContactCreate(
            name="Frank",
            email="frank@example.com",
            phone="555-1111",
            company="Frank Co",
            notes="Frank note",
        )
    )
    updated = update(contact.id, ContactUpdate(name="Frank Updated"))
    assert updated is not None
    assert updated.name == "Frank Updated"
    assert updated.email == "frank@example.com"
    assert updated.phone == "555-1111"
    assert updated.company == "Frank Co"
    assert updated.notes == "Frank note"


def test_update_bumps_updated_at(db):
    contact = create(ContactCreate(name="Grace"))
    original_updated_at = contact.updated_at
    time.sleep(1.1)
    updated = update(contact.id, ContactUpdate(name="Grace Updated"))
    assert updated is not None
    assert updated.updated_at != original_updated_at


def test_update_empty_bumps_updated_at(db):
    contact = create(ContactCreate(name="Grant"))
    original_updated_at = contact.updated_at
    time.sleep(1.1)
    updated = update(contact.id, ContactUpdate())
    assert updated is not None
    assert updated.name == "Grant"
    assert updated.updated_at != original_updated_at


def test_update_nonexistent_id(db):
    result = update("nonexistent-id-67890", ContactUpdate(name="Nobody"))
    assert result is None


def test_delete_existing(db):
    contact = create(ContactCreate(name="Hannah"))
    assert delete(contact.id) is True
    assert get_by_id(contact.id) is None


def test_delete_nonexistent(db):
    assert delete("nonexistent-id-abcde") is False


def test_search_by_name_exact(db):
    create(ContactCreate(name="Isaac Newton"))
    create(ContactCreate(name="Isaac Asimov"))
    results = search_by_name("Isaac Newton")
    assert len(results) == 1
    assert results[0].name == "Isaac Newton"


def test_search_by_name_substring(db):
    create(ContactCreate(name="Alice Smith"))
    create(ContactCreate(name="Bob Jones"))
    create(ContactCreate(name="Alicia Keys"))
    results = search_by_name("Smith")
    assert len(results) == 1
    assert results[0].name == "Alice Smith"


def test_search_by_name_prefix(db):
    create(ContactCreate(name="Isaac"))
    create(ContactCreate(name="Isaiah"))
    create(ContactCreate(name="Ivan"))
    results = search_by_name("Isa")
    assert len(results) == 2
    assert {c.name for c in results} == {"Isaac", "Isaiah"}


def test_search_by_name_case_insensitive(db):
    create(ContactCreate(name="Alice Smith"))
    results_lower = search_by_name("alice")
    results_upper = search_by_name("ALICE")
    results_mixed = search_by_name("AlIcE")
    assert len(results_lower) == 1
    assert len(results_upper) == 1
    assert len(results_mixed) == 1
    assert results_lower[0].name == "Alice Smith"


def test_search_by_name_no_matches(db):
    create(ContactCreate(name="Karen"))
    results = search_by_name("ZZZZZZ")
    assert results == []


def test_search_by_name_empty_query(db):
    create(ContactCreate(name="Larry"))
    results = search_by_name("")
    assert results == []
