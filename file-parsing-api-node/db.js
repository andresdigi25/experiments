// db.js
const { Pool } = require('pg');
const config = require('./config');

// Create a pool of PostgreSQL clients
const pool = new Pool({
  host: process.env.DB_HOST || config.database.host,
  port: process.env.DB_PORT || config.database.port,
  database: process.env.DB_NAME || config.database.name,
  user: process.env.DB_USER || config.database.user,
  password: process.env.DB_PASSWORD || config.database.password,
});

// Initialize database by creating the necessary tables
const initializeDatabase = async () => {
  try {
    const client = await pool.connect();
    try {
      // Create the records table if it doesn't exist
      await client.query(`
        CREATE TABLE IF NOT EXISTS records (
          id SERIAL PRIMARY KEY,
          name VARCHAR(255),
          address1 VARCHAR(255),
          city VARCHAR(255),
          state VARCHAR(50),
          zip VARCHAR(20),
          auth_id VARCHAR(100) UNIQUE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      console.log('Database initialized successfully');
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error initializing database:', error);
    // Continue running even if database init fails
  }
};

// Save records to the database
const saveRecords = async (records) => {
  const client = await pool.connect();
  let savedCount = 0;

  try {
    await client.query('BEGIN');
    
    for (const record of records) {
      try {
        const result = await client.query(
          `INSERT INTO records(name, address1, city, state, zip, auth_id)
           VALUES($1, $2, $3, $4, $5, $6)
           ON CONFLICT (auth_id) 
           DO UPDATE SET 
             name = $1,
             address1 = $2,
             city = $3,
             state = $4,
             zip = $5
           RETURNING id`,
          [record.name, record.address1, record.city, record.state, record.zip, record.authId]
        );
        
        if (result.rows.length > 0) {
          savedCount++;
        }
      } catch (recordError) {
        console.error('Error saving record:', recordError, record);
        // Continue with other records if one fails
      }
    }
    
    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }

  return { success: true, count: savedCount };
};

module.exports = {
  pool,
  initializeDatabase,
  saveRecords,
};