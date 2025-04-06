import snowflake.connector
import boto3
import pandas as pd
import os
import io
from dotenv import load_dotenv
from faker import Faker
import numpy as np
import uuid
from datetime import datetime, timedelta
import time

# Load environment variables from .env file
load_dotenv()

# Snowflake connection parameters
snowflake_config = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA')
}

# AWS S3 configuration
s3_config = {
    'bucket_name': os.getenv('S3_BUCKET_NAME'),
    'prefix': os.getenv('S3_PREFIX', 'data/'),  # folder path in the bucket
    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'region_name': os.getenv('AWS_REGION', 'us-east-1')
}

# Target Snowflake table
target_table = os.getenv('SNOWFLAKE_TARGET_TABLE', 'CUSTOMER_ORDERS')

# Data generation settings
data_config = {
    'num_records': int(os.getenv('NUM_RECORDS', 100000)),
    'num_files': int(os.getenv('NUM_FILES', 5)),
    'file_format': os.getenv('FILE_FORMAT', 'csv')  # csv, parquet
}

def generate_fake_data(records_per_file):
    """Generate fake customer order data."""
    faker = Faker()
    
    print(f"Generating {records_per_file} fake records...")
    
    # Create unique customer IDs
    customer_ids = [str(uuid.uuid4()) for _ in range(int(records_per_file * 0.2))]
    
    # Generate random order dates within the last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = []
    for _ in range(records_per_file):
        customer_id = np.random.choice(customer_ids)
        order_date = faker.date_time_between(start_date=start_date, end_date=end_date)
        
        record = {
            'ORDER_ID': str(uuid.uuid4()),
            'CUSTOMER_ID': customer_id,
            'ORDER_DATE': order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'PRODUCT_ID': faker.random_int(min=1000, max=9999),
            'PRODUCT_NAME': faker.word().title() + ' ' + faker.word().title(),
            'CATEGORY': faker.random_element(elements=('Electronics', 'Clothing', 'Home', 'Books', 'Sports')),
            'QUANTITY': faker.random_int(min=1, max=10),
            'UNIT_PRICE': round(faker.random_number(digits=2) + faker.random.random(), 2),
            'TOTAL_AMOUNT': None,  # Will calculate below
            'PAYMENT_METHOD': faker.random_element(elements=('Credit Card', 'PayPal', 'Bank Transfer', 'Cash')),
            'SHIPPING_ADDRESS': faker.address().replace('\n', ', '),
            'STATUS': faker.random_element(elements=('Pending', 'Shipped', 'Delivered', 'Cancelled')),
            'CREATED_AT': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Calculate total amount
        record['TOTAL_AMOUNT'] = round(record['QUANTITY'] * record['UNIT_PRICE'], 2)
        
        data.append(record)
    
    df = pd.DataFrame(data)
    print(f"Generated DataFrame with shape: {df.shape}")
    return df

def upload_dataframe_to_s3(df, file_index, file_format='csv'):
    """Upload a pandas DataFrame to S3."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_config['aws_access_key_id'],
        aws_secret_access_key=s3_config['aws_secret_access_key'],
        region_name=s3_config['region_name']
    )
    
    timestamp = int(time.time())
    if file_format.lower() == 'csv':
        file_name = f"{s3_config['prefix']}orders_{timestamp}_{file_index}.csv"
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        content = buffer.getvalue()
        s3_client.put_object(
            Bucket=s3_config['bucket_name'],
            Key=file_name,
            Body=content
        )
    elif file_format.lower() == 'parquet':
        file_name = f"{s3_config['prefix']}orders_{timestamp}_{file_index}.parquet"
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        content = buffer.getvalue()
        s3_client.put_object(
            Bucket=s3_config['bucket_name'],
            Key=file_name,
            Body=content
        )
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    print(f"Uploaded {file_name} to S3")
    return file_name

def generate_and_upload_data():
    """Generate fake data and upload it to S3 in multiple files."""
    records_per_file = data_config['num_records'] // data_config['num_files']
    uploaded_files = []
    
    for i in range(data_config['num_files']):
        print(f"Processing file {i+1}/{data_config['num_files']}...")
        df = generate_fake_data(records_per_file)
        file_name = upload_dataframe_to_s3(df, i+1, data_config['file_format'])
        uploaded_files.append(file_name)
    
    return uploaded_files

def connect_to_snowflake():
    """Establish connection to Snowflake."""
    try:
        conn = snowflake.connector.connect(
            user=snowflake_config['user'],
            password=snowflake_config['password'],
            account=snowflake_config['account'],
            warehouse=snowflake_config['warehouse'],
            database=snowflake_config['database'],
            schema=snowflake_config['schema']
        )
        print("Successfully connected to Snowflake!")
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        raise

def setup_snowflake_objects(conn):
    """Create Snowflake table and stage if they don't exist."""
    cursor = conn.cursor()
    try:
        # Create table if it doesn't exist
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
            ORDER_ID VARCHAR(36) PRIMARY KEY,
            CUSTOMER_ID VARCHAR(36) NOT NULL,
            ORDER_DATE TIMESTAMP_NTZ NOT NULL,
            PRODUCT_ID INTEGER NOT NULL,
            PRODUCT_NAME VARCHAR(255) NOT NULL,
            CATEGORY VARCHAR(50),
            QUANTITY INTEGER NOT NULL,
            UNIT_PRICE DECIMAL(10,2) NOT NULL,
            TOTAL_AMOUNT DECIMAL(10,2) NOT NULL,
            PAYMENT_METHOD VARCHAR(50),
            SHIPPING_ADDRESS VARCHAR(500),
            STATUS VARCHAR(20) NOT NULL,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """)
        print(f"Table {target_table} created or already exists")
        
        # Create file format
        if data_config['file_format'].lower() == 'csv':
            cursor.execute("""
            CREATE FILE FORMAT IF NOT EXISTS CSV_FORMAT
                TYPE = 'CSV'
                FIELD_DELIMITER = ','
                SKIP_HEADER = 1
                NULL_IF = ('NULL', 'null')
                FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            """)
            file_format_name = "CSV_FORMAT"
        else:  # parquet
            cursor.execute("""
            CREATE FILE FORMAT IF NOT EXISTS PARQUET_FORMAT
                TYPE = 'PARQUET'
            """)
            file_format_name = "PARQUET_FORMAT"
        
        # Create stage
        stage_name = 'MY_S3_STAGE'
        s3_url = f's3://{s3_config["bucket_name"]}/{s3_config["prefix"]}'
        
        # Check if stage exists
        cursor.execute(f"SHOW STAGES LIKE '{stage_name}'")
        stages = cursor.fetchall()
        
        if not stages:
            cursor.execute(f"""
            CREATE STAGE {stage_name}
              URL = '{s3_url}'
              CREDENTIALS = (AWS_KEY_ID='{s3_config['aws_access_key_id']}' 
                            AWS_SECRET_KEY='{s3_config['aws_secret_access_key']}')
              FILE_FORMAT = {file_format_name}
            """)
            print(f"Stage {stage_name} created successfully")
        else:
            print(f"Stage {stage_name} already exists")
        
        return stage_name, file_format_name
    except Exception as e:
        print(f"Error setting up Snowflake objects: {e}")
        raise
    finally:
        cursor.close()

def load_data_to_snowflake(conn, stage_name, file_format_name, files=None):
    """Load data from S3 stage to Snowflake table."""
    cursor = conn.cursor()
    try:
        # Resize warehouse for better performance
        cursor.execute(f"ALTER WAREHOUSE {snowflake_config['warehouse']} SET WAREHOUSE_SIZE = 'LARGE' AUTO_SUSPEND = 60")
        
        start_time = time.time()
        
        if files:
            # Get only the file names (not full paths)
            file_names = [os.path.basename(file) for file in files]
            file_pattern = '|'.join(file_names).replace('.', '\.')
            
            print(f"Loading files matching pattern: {file_pattern}")
            cursor.execute(f"""
            COPY INTO {target_table}
            FROM @{stage_name}
            PATTERN = '.*({file_pattern})'
            FILE_FORMAT = {file_format_name}
            """)
        else:
            # Load all files with the right extension
            extension = '.csv' if data_config['file_format'].lower() == 'csv' else '.parquet'
            print(f"Loading all {extension} files from stage")
            cursor.execute(f"""
            COPY INTO {target_table}
            FROM @{stage_name}
            PATTERN = '.*\\{extension}'
            FILE_FORMAT = {file_format_name}
            """)
        
        result = cursor.fetchall()
        
        # Calculate stats
        total_files = len(result)
        total_rows = sum(row[3] for row in result)  # Rows loaded column
        elapsed_time = time.time() - start_time
        rows_per_second = int(total_rows / elapsed_time) if elapsed_time > 0 else 0
        
        print(f"Load completed in {elapsed_time:.2f} seconds")
        print(f"Loaded {total_rows} rows from {total_files} files")
        print(f"Performance: {rows_per_second} rows per second")
        
        # Resize warehouse back to original size
        cursor.execute(f"ALTER WAREHOUSE {snowflake_config['warehouse']} SET WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60")
        
        return result
    except Exception as e:
        print(f"Error loading data to Snowflake: {e}")
        raise
    finally:
        cursor.close()

def validate_data_load(conn):
    """Validate that data was loaded correctly."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        count = cursor.fetchone()[0]
        print(f"Total records in {target_table}: {count}")
        
        cursor.execute(f"SELECT MIN(ORDER_DATE), MAX(ORDER_DATE) FROM {target_table}")
        date_range = cursor.fetchone()
        print(f"Date range: {date_range[0]} to {date_range[1]}")
        
        cursor.execute(f"SELECT COUNT(DISTINCT CUSTOMER_ID) FROM {target_table}")
        customer_count = cursor.fetchone()[0]
        print(f"Distinct customers: {customer_count}")
        
        return count
    except Exception as e:
        print(f"Error validating data load: {e}")
        raise
    finally:
        cursor.close()

def main():
    """Main function to orchestrate the entire process."""
    print("Starting data pipeline: Generate → S3 → Snowflake")
    
    try:
        # Step 1: Generate fake data and upload to S3
        print("\n=== STEP 1: GENERATE DATA AND UPLOAD TO S3 ===")
        uploaded_files = generate_and_upload_data()
        print(f"Successfully uploaded {len(uploaded_files)} files to S3")
        
        # Sleep briefly to ensure S3 consistency
        time.sleep(5)
        
        # Step 2: Connect to Snowflake and set up objects
        print("\n=== STEP 2: SET UP SNOWFLAKE OBJECTS ===")
        conn = connect_to_snowflake()
        stage_name, file_format_name = setup_snowflake_objects(conn)
        
        # Step 3: Load data from S3 to Snowflake
        print("\n=== STEP 3: LOAD DATA FROM S3 TO SNOWFLAKE ===")
        load_results = load_data_to_snowflake(conn, stage_name, file_format_name, uploaded_files)
        
        # Step 4: Validate the loaded data
        print("\n=== STEP 4: VALIDATE LOADED DATA ===")
        record_count = validate_data_load(conn)
        
        print("\n=== PIPELINE COMPLETED SUCCESSFULLY ===")
        print(f"Total records loaded: {record_count}")
        print(f"Files processed: {len(uploaded_files)}")
        
    except Exception as e:
        print(f"ERROR: Pipeline failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Snowflake connection closed")

if __name__ == "__main__":
    main()


#pip install snowflake-connector-python boto3 pandas python-dotenv faker numpy pyarrow