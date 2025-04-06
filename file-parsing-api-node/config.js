// config.js
module.exports = {
    // Database configuration
    database: {
      // Replace with your actual database config
      host: 'localhost',
      port: 5432,
      name: 'datastore',
      user: 'user',
      password: 'password',
    },
    
    // Field mapping configurations
    fieldMappings: {
      // Default mapping that works as a fallback
      default: {
        name: ['name', 'full_name', 'customer_name', 'client_name'],
        address1: ['address', 'address1', 'street_address', 'street'],
        city: ['city', 'town'],
        state: ['state', 'province', 'region'],
        zip: ['zip', 'zipcode', 'postal_code', 'postalcode', 'zip_code'],
        authId: ['auth_id', 'authid', 'authorization_id', 'auth', 'id']
      },
      
      // Example of a vendor-specific mapping
      vendor1: {
        name: ['customer'],
        address1: ['primary_address'],
        city: ['customer_city'],
        state: ['customer_state'],
        zip: ['customer_zip'],
        authId: ['customer_id']
      },
      
      // You can add more source-specific mappings here
    },
    
    // Validation rules
    validation: {
      // Required fields for a record to be considered valid
      requiredFields: ['name', 'authId'],
      
      // Optional validation rules (examples)
      rules: {
        zip: {
          pattern: /^\d{5}(-\d{4})?$/,
          message: 'ZIP code must be 5 digits or 5+4 format'
        },
        state: {
          maxLength: 2,
          message: 'State should be a 2-letter code'
        }
      }
    }
  };