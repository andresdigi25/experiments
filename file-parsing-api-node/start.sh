#!/bin/bash

# Create sample_files directory if it doesn't exist
mkdir -p sample_files

# Copy sample files to the sample_files directory
cat > sample_files/sample_data.csv << 'EOF'
full_name,street_address,city,state,zipcode,auth_id
John Doe,123 Main St,New York,NY,10001,AUTH001
Jane Smith,456 Park Ave,Los Angeles,CA,90001,AUTH002
Robert Johnson,789 Broadway,Chicago,IL,60601,AUTH003
Emily Williams,321 Oak St,Houston,TX,77001,AUTH004
Michael Brown,654 Pine Rd,Phoenix,AZ,85001,AUTH005
EOF

cat > sample_files/vendor1_data.csv << 'EOF'
customer,primary_address,customer_city,customer_state,customer_zip,customer_id
William Davis,852 Cedar Lane,Miami,FL,33101,VEN1_001
Linda Miller,741 Elm Street,Seattle,WA,98101,VEN1_002
James Wilson,963 Maple Drive,Denver,CO,80201,VEN1_003
Jennifer Moore,159 Walnut Ave,Boston,MA,02101,VEN1_004
David Taylor,357 Birch Blvd,Atlanta,GA,30301,VEN1_005
EOF

cat > sample_files/sample_data.json << 'EOF'
[
  {
    "name": "Thomas Anderson",
    "address": "555 Matrix St",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "authorization_id": "JSON001"
  },
  {
    "name": "Sarah Connor",
    "address": "888 Skynet Ave",
    "city": "San Diego",
    "state": "CA",
    "postal_code": "92101",
    "authorization_id": "JSON002"
  },
  {
    "name": "John Wick",
    "address": "777 Continental Blvd",
    "city": "New York",
    "state": "NY",
    "postal_code": "10036",
    "authorization_id": "JSON003"
  },
  {
    "name": "Ellen Ripley",
    "address": "123 Nostromo St",
    "city": "Dallas",
    "state": "TX",
    "postal_code": "75201",
    "authorization_id": "JSON004"
  },
  {
    "name": "Tony Stark",
    "address": "10880 Malibu Point",
    "city": "Malibu",
    "state": "CA",
    "postal_code": "90265",
    "authorization_id": "JSON005"
  }
]
EOF

cat > sample_files/vendor2_data.json << 'EOF'
[
  {
    "client_name": "Hermione Granger",
    "billing_address": "12 Grimmauld Place",
    "billing_city": "London",
    "billing_state": "UK",
    "billing_zip": "SW1A 1AA",
    "client_code": "V2_001"
  },
  {
    "client_name": "Ron Weasley",
    "billing_address": "The Burrow",
    "billing_city": "Ottery St Catchpole",
    "billing_state": "UK",
    "billing_zip": "EX11 1DJ",
    "client_code": "V2_002"
  },
  {
    "client_name": "Harry Potter",
    "billing_address": "4 Privet Drive",
    "billing_city": "Little Whinging",
    "billing_state": "UK",
    "billing_zip": "GU25 4PH",
    "client_code": "V2_003"
  },
  {
    "client_name": "Albus Dumbledore",
    "billing_address": "Hogwarts School",
    "billing_city": "Hogsmeade",
    "billing_state": "UK",
    "billing_zip": "IV27 4NH",
    "client_code": "V2_004"
  },
  {
    "client_name": "Severus Snape",
    "billing_address": "Spinner's End",
    "billing_city": "Cokeworth",
    "billing_state": "UK",
    "billing_zip": "M1 1AE",
    "client_code": "V2_005"
  }
]
EOF

cat > sample_files/sample_data.txt << 'EOF'
client_name	street	town	region	zip_code	id
Bruce Wayne	1 Wayne Manor	Gotham	NJ	07101	TXT001
Clark Kent	344 Clinton St	Metropolis	NY	10001	TXT002
Diana Prince	1720 H St NW	Washington	DC	20006	TXT003
Peter Parker	20 Ingram St	Queens	NY	11375	TXT004
Steve Rogers	569 Leaman Place	Brooklyn	NY	11201	TXT005
EOF

# Create uploads directory if it doesn't exist
mkdir -p uploads
chmod 777 uploads

# Start the application with Docker Compose
echo "Starting the application..."
docker-compose up --build