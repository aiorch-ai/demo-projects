from __future__ import annotations

import time

import pytest

from contacts.models import ContactCreate, ContactUpdate
from contacts.repository import (
    create,
    delete,
    get_by_id,
    list_all,
    search_by_name,
    update,
)


def test_create(fresh_db):
    data = ContactCreate(
        name="Alice",
        email="alice@example.com",
        phone="555-1234",
        company="Example Inc",
        notes="A note",
    )
    contact = create(data)
    assert contact.name == "Alice"
    assert contact.email == "alice@example.com"
    assert contact.phone == "555-1234"
    assert contact.company == "Example Inc"
    assert contact.notes == "A note"
    assert contact.id
    assert contact.created_at
    assert contact.updated_at

    fetched = get_by_id(contact.id)
    assert fetched is not None
    assert fetched.name == "Alice"


def test_create_minimal(fresh_db):
    data = ContactCreate(name="Bob")
    contact = create(data)
    assert contact.name == "Bob"
    assert contact.email is None
    assert contact.phone is None
    assert contact.company is None
    assert contact.notes is None


def test_get_by_id_found(fresh_db):
    contact = create(ContactCreate(name="Charlie", email="charlie@example.com"))
    fetched = get_by_id(contact.id)
    assert fetched is not None
    assert fetched.id == contact.id
    assert fetched.name == "Charlie"
    assert fetched.email == "charlie@example.com"


def test_get_by_id_not_found(fresh_db):
    result = get_by_id("nonexistent")
    assert result is None


def test_list_all_empty(fresh_db):
    result = list_all()
    assert result == []


def test_list_all_ordered_by_name(fresh_db):
    create(ContactCreate(name="Zebra"))
    create(ContactCreate(name="Apple"))
    create(ContactCreate(name="Mango"))
    contacts = list_all()
    assert len(contacts) == 3
    assert [c.name for c in contacts] == ["Apple", "Mango", "Zebra"]


def test_update_full(fresh_db):
    contact = create(
        ContactCreate(
            name="Dana",
            email="dana@example.com",
            phone="555-0000",
            company="Old Co",
            notes="Old note",
        )
    )
    updated = update(
        contact.id,
        ContactUpdate(
            name="Dana Updated",
            email="dana.new@example.com",
            phone="555-9999",
            company="New Co",
            notes="New note",
        ),
    )
    assert updated is not None
    assert updated.name == "Dana Updated"
    assert updated.email == "dana.new@example.com"
    assert updated.phone == "555-9999"
    assert updated.company == "New Co"
    assert updated.notes == "New note"
    assert updated.id == contact.id


def test_update_partial(fresh_db):
    contact = create(
        ContactCreate(
            name="Eve",
            email="eve@example.com",
            phone="555-1111",
            company="Eve Co",
            notes="Eve note",
        )
    )
    updated = update(contact.id, ContactUpdate(name="Eve Updated"))
    assert updated is not None
    assert updated.name == "Eve Updated"
    assert updated.email == "eve@example.com"
    assert updated.phone == "555-1111"
    assert updated.company == "Eve Co"
    assert updated.notes == "Eve note"


def test_update_empty_bumps_updated_at(fresh_db):
    contact = create(ContactCreate(name="Frank"))
    original_updated_at = contact.updated_at
    time.sleep(1.1)
    updated = update(contact.id, ContactUpdate())
    assert updated is not None
    assert updated.name == "Frank"
    assert updated.updated_at != original_updated_at


def test_update_not_found(fresh_db):
    result = update("nonexistent", ContactUpdate(name="Nobody"))
    assert result is None


def test_delete_found(fresh_db):
    contact = create(ContactCreate(name="Grace"))
    assert delete(contact.id) is True
    assert get_by_id(contact.id) is None


def test_delete_not_found(fresh_db):
    assert delete("nonexistent") is False


def test_search_by_name_exact(fresh_db):
    create(ContactCreate(name="Hannah"))
    create(ContactCreate(name="Henry"))
    results = search_by_name("Hannah")
    assert len(results) == 1
    assert results[0].name == "Hannah"


def test_search_by_name_prefix(fresh_db):
    create(ContactCreate(name="Isaac"))
    create(ContactCreate(name="Isaiah"))
    create(ContactCreate(name="Ivan"))
    results = search_by_name("Isa")
    assert len(results) == 2
    assert {c.name for c in results} == {"Isaac", "Isaiah"}


def test_search_by_name_case_insensitive(fresh_db):
    create(ContactCreate(name="Jack"))
    results_lower = search_by_name("jack")
    results_upper = search_by_name("JACK")
    results_mixed = search_by_name("JaCk")
    assert len(results_lower) == 1
    assert len(results_upper) == 1
    assert len(results_mixed) == 1


def test_search_by_name_empty_query(fresh_db):
    create(ContactCreate(name="Karen"))
    results = search_by_name("")
    assert results == []


def test_search_by_name_no_match(fresh_db):
    create(ContactCreate(name="Larry"))
    results = search_by_name("ZZZZZZ")
    assert results == []
