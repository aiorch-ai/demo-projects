from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from contacts.models import Contact, ContactCreate, ContactUpdate
from contacts.repository import create, delete, get_by_id, list_all, search_by_name, update

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/search", response_model=list[Contact])
def search_contacts(q: str) -> list[Contact]:
    return search_by_name(q)


@router.post("", response_model=Contact, status_code=201)
def create_contact(data: ContactCreate) -> Contact:
    return create(data)


@router.get("", response_model=list[Contact])
def get_contacts() -> list[Contact]:
    return list_all()


@router.get("/{contact_id}", response_model=Contact)
def get_contact(contact_id: str) -> Contact:
    contact = get_by_id(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=Contact)
def update_contact(contact_id: str, data: ContactUpdate) -> Contact:
    contact = update(contact_id, data)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: str) -> Response:
    if not delete(contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return Response(status_code=204)
