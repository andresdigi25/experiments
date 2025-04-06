// server.js
const express = require('express');
const multer = require('multer');
const csv = require('csv-parser');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const { Readable } = require('stream');
const config = require('./config');
const app = express();
const port = process.env.PORT || 3000;

// Configure multer for file uploads
const upload = multer({ dest: 'uploads/' });

// Import database helper
const db = require('./db');

// Field mapping configuration
// This defines how to map various source columns to your target schema
const fieldMappings = config.fieldMappings;

// File type detection
const detectFileType = (filename) => {
  const ext = path.extname(filename).toLowerCase();
  switch (ext) {
    case '.csv':
      return 'csv';
    case '.xlsx':
    case '.xls':
      return 'excel';
    case '.json':
      return 'json';
    case '.txt':
      return 'text';
    default:
      return 'unknown';
  }
};

// Normalize field names using the mapping configuration
const normalizeRecord = (record, mappingKey = 'default') => {
  const mapping = fieldMappings[mappingKey] || fieldMappings.default;
  const normalizedRecord = {};
  
  // Initialize with nulls to ensure all fields exist
  Object.keys(mapping).forEach(targetField => {
    normalizedRecord[targetField] = null;
  });
  
  // Process the record fields
  Object.entries(record).forEach(([sourceField, value]) => {
    const sourceFieldLower = sourceField.toLowerCase().trim();
    
    // Check each target field
    Object.entries(mapping).forEach(([targetField, possibleSourceFields]) => {
      if (
        possibleSourceFields.some(f => 
          f.toLowerCase() === sourceFieldLower ||
          sourceFieldLower.includes(f.toLowerCase())
        )
      ) {
        normalizedRecord[targetField] = value;
      }
    });
  });
  
  return normalizedRecord;
};

// CSV Parser
const parseCSV = (filePath) => {
  return new Promise((resolve, reject) => {
    const results = [];
    
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => results.push(data))
      .on('end', () => {
        resolve(results);
      })
      .on('error', (error) => {
        reject(error);
      });
  });
};

// Excel Parser
const parseExcel = (filePath) => {
  return new Promise((resolve, reject) => {
    try {
      const workbook = xlsx.readFile(filePath);
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const data = xlsx.utils.sheet_to_json(worksheet);
      resolve(data);
    } catch (error) {
      reject(error);
    }
  });
};

// JSON Parser
const parseJSON = (filePath) => {
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, 'utf8', (err, data) => {
      if (err) {
        reject(err);
        return;
      }
      
      try {
        const jsonData = JSON.parse(data);
        const records = Array.isArray(jsonData) ? jsonData : [jsonData];
        resolve(records);
      } catch (error) {
        reject(error);
      }
    });
  });
};

// Text Parser (basic example - assumes tab or comma delimited with header row)
const parseText = (filePath) => {
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, 'utf8', (err, data) => {
      if (err) {
        reject(err);
        return;
      }
      
      try {
        // Detect delimiter (simple detection)
        const firstLine = data.split('\n')[0];
        let delimiter = '\t';
        if (firstLine.includes(',') && !firstLine.includes('\t')) {
          delimiter = ',';
        }
        
        // Parse the data
        const lines = data.trim().split('\n');
        const headers = lines[0].split(delimiter).map(h => h.trim());
        const records = [];
        
        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(delimiter);
          const record = {};
          
          headers.forEach((header, index) => {
            record[header] = values[index] ? values[index].trim() : null;
          });
          
          records.push(record);
        }
        
        resolve(records);
      } catch (error) {
        reject(error);
      }
    });
  });
};

// Main file processing function
const processFile = async (filePath, filename, source = 'default') => {
  const fileType = detectFileType(filename);
  let records;
  
  switch (fileType) {
    case 'csv':
      records = await parseCSV(filePath);
      break;
    case 'excel':
      records = await parseExcel(filePath);
      break;
    case 'json':
      records = await parseJSON(filePath);
      break;
    case 'text':
      records = await parseText(filePath);
      break;
    default:
      throw new Error(`Unsupported file type: ${fileType}`);
  }
  
  // Normalize all records using the appropriate mapping
  const normalizedRecords = records.map(record => normalizeRecord(record, source));
  
  // Validate records
  const validRecords = normalizedRecords.filter(record => {
    // Check required fields from config
    return config.validation.requiredFields.every(field => record[field]);
  });
  
  return {
    total: records.length,
    valid: validRecords.length,
    invalid: records.length - validRecords.length,
    records: validRecords
  };
};

// API Endpoints
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    const { source } = req.body;
    const result = await processFile(req.file.path, req.file.originalname, source);
    
    // Connect to database and save the processed records
    const saveResult = await db.saveRecords(result.records);
    
    // Clean up the uploaded file
    fs.unlinkSync(req.file.path);
    
    res.status(200).json({
      message: 'File processed successfully',
      summary: {
        totalRecords: result.total,
        validRecords: result.valid,
        invalidRecords: result.invalid,
        savedRecords: saveResult.count
      }
    });
  } catch (error) {
    console.error('Error processing file:', error);
    res.status(500).json({ error: error.message });
  }
});

// Define a mapping configuration endpoint
app.post('/api/mappings', express.json(), (req, res) => {
  const { name, mappings } = req.body;
  
  if (!name || !mappings) {
    return res.status(400).json({ error: 'Name and mappings are required' });
  }
  
  fieldMappings[name] = mappings;
  res.status(201).json({ message: 'Mapping configuration created', name });
});

// Get all mapping configurations
app.get('/api/mappings', (req, res) => {
  res.status(200).json(fieldMappings);
});

// Initialize the database before starting the server
db.initializeDatabase()
  .then(() => {
    // Start the server
    app.listen(port, () => {
      console.log(`Server is running on port ${port}`);
    });
  })
  .catch(err => {
    console.error('Failed to initialize the application:', err);
    process.exit(1);
  });