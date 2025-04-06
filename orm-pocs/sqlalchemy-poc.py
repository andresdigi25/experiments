from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from marshmallow import Schema, fields
import csv
from sqlalchemy.orm import sessionmaker
import click


Base = declarative_base()

class Address(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip = Column(String, nullable=False)
    client_id = Column(Integer, nullable=False)
    status = Column(String, default='ACTIVE')

# Create an SQLite database
engine = create_engine('sqlite:///addresses.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class AddressSchema(Schema):
    name = fields.Str(required=True)
    address = fields.Str(required=True)
    state = fields.Str(required=True)
    zip = fields.Str(required=True)
    client_id = fields.Int(required=True)


class AddressParser:
    def __init__(self, file_path, client_id):
        self.file_path = file_path
        self.client_id = client_id
        self.schema = AddressSchema()
        self.session = Session()

    def validate(self):
        errors = []
        with open(self.file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader, start=1):
                row['client_id'] = self.client_id
                errors.extend(self.schema.validate(row, partial=False))
        return errors

    def parse(self):
        addresses = []
        with open(self.file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row['client_id'] = self.client_id
                address = self.schema.load(row)
                addresses.append(address)
        return addresses

    def store(self, addresses):
        for address in addresses:
            self.session.add(Address(**address))
        self.session.commit()

    def process(self):
        errors = self.validate()
        if errors:
            print("Validation errors found:", errors)
            return
        addresses = self.parse()
        self.store(addresses)
        print(f"Successfully processed {len(addresses)} addresses.")



@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('client_id', type=int)
def process_file(file_path, client_id):
    parser = AddressParser(file_path, client_id)
    parser.process()

if __name__ == '__main__':
    process_file()

