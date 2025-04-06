const express = require('express');
const bodyParser = require('body-parser');
const AWS = require('aws-sdk');

const app = express();
const port = 3000;

app.use(bodyParser.json());

AWS.config.update({
  region: 'us-west-2', // Update to your region
});

const dynamoDb = new AWS.DynamoDB.DocumentClient();
const TableName = 'teams';

// Create a new team
app.post('/teams', (req, res) => {
  const { name, members } = req.body;
  const params = {
    TableName,
    Item: {
      name,
      members,
    },
  };

  dynamoDb.put(params, (err) => {
    if (err) {
      res.status(500).json({ error: 'Could not create team' });
    } else {
      res.status(201).json({ message: 'Team created successfully' });
    }
  });
});

// Get all teams
app.get('/teams', (req, res) => {
  const params = {
    TableName,
  };

  dynamoDb.scan(params, (err, data) => {
    if (err) {
      res.status(500).json({ error: 'Could not retrieve teams' });
    } else {
      res.status(200).json(data.Items);
    }
  });
});

// Get a team by name
app.get('/teams/:name', (req, res) => {
  const params = {
    TableName,
    Key: {
      name: req.params.name,
    },
  };

  dynamoDb.get(params, (err, data) => {
    if (err) {
      res.status(500).json({ error: 'Could not retrieve team' });
    } else {
      res.status(200).json(data.Item);
    }
  });
});

// Update a team
app.put('/teams/:name', (req, res) => {
  const { members } = req.body;
  const params = {
    TableName,
    Key: {
      name: req.params.name,
    },
    UpdateExpression: 'set members = :members',
    ExpressionAttributeValues: {
      ':members': members,
    },
    ReturnValues: 'UPDATED_NEW',
  };

  dynamoDb.update(params, (err, data) => {
    if (err) {
      res.status(500).json({ error: 'Could not update team' });
    } else {
      res.status(200).json(data.Attributes);
    }
  });
});

// Delete a team
app.delete('/teams/:name', (req, res) => {
  const params = {
    TableName,
    Key: {
      name: req.params.name,
    },
  };

  dynamoDb.delete(params, (err) => {
    if (err) {
      res.status(500).json({ error: 'Could not delete team' });
    } else {
      res.status(200).json({ message: 'Team deleted successfully' });
    }
  });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});