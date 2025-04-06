from sqlmodel import Session, select
from models import Resource1

def create_resource(session: Session, resource: Resource1) -> Resource1:
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return resource

def get_resource(session: Session, resource_id: int) -> Resource1:
    return session.get(Resource1, resource_id)

def update_resource(session: Session, resource_id: int, resource_data: Resource1) -> Resource1:
    resource = session.get(Resource1, resource_id)
    if not resource:
        return None
    for key, value in resource_data.dict(exclude_unset=True).items():
        setattr(resource, key, value)
    session.commit()
    session.refresh(resource)
    return resource

def delete_resource(session: Session, resource_id: int) -> None:
    resource = session.get(Resource1, resource_id)
    if resource:
        session.delete(resource)
        session.commit()