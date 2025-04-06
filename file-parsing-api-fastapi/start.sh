#!/bin/bash

# Create directories if they don't exist
mkdir -p uploads
mkdir -p sample_files

# Copy sample files
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

cat > sample_files/sample_data.txt << 'EOF'
client_name	street	town	region	zip_code	id
Bruce Wayne	1 Wayne Manor	Gotham	NJ	07101	TXT001
Clark Kent	344 Clinton St	Metropolis	NY	10001	TXT002
Diana Prince	1720 H St NW	Washington	DC	20006	TXT003
Peter Parker	20 Ingram St	Queens	NY	11375	TXT004
Steve Rogers	569 Leaman Place	Brooklyn	NY	11201	TXT005
EOF

# Set permissions
chmod 777 uploads
chmod +x test_api.sh

# Start the application with Docker Compose
echo "Starting the application..."
docker-compose up --build