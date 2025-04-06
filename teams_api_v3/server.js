const express = require('express');
const bodyParser = require('body-parser');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, ScanCommand, GetCommand, UpdateCommand, DeleteCommand } = require('@aws-sdk/lib-dynamodb');

const app = express();
const port = 3000;

app.use(bodyParser.json());

const client = new DynamoDBClient({ region: 'us-east-1' }); // Update to your region
const dynamoDb = DynamoDBDocumentClient.from(client);
const TableName = 'teams';

// Create a new team
app.post('/teams', async (req, res) => {
  const { name, members } = req.body;
  const params = {
    TableName,
    Item: {
      name,
      members,
    },
  };

  try {
    await dynamoDb.send(new PutCommand(params));
    res.status(201).json({ message: 'Team created successfully' });
  } catch (err) {
    res.status(500).json({ error: 'Could not create team' });
  }
});

// Get all teams
app.get('/teams', async (req, res) => {
  const params = {
    TableName,
  };

  try {
    const data = await dynamoDb.send(new ScanCommand(params));
    res.status(200).json(data.Items);
  } catch (err) {
    res.status(500).json({ error: 'Could not retrieve teams' });
  }
});

// Get a team by name
app.get('/teams/:name', async (req, res) => {
  const params = {
    TableName,
    Key: {
      name: req.params.name,
    },
  };

  try {
    const data = await dynamoDb.send(new GetCommand(params));
    res.status(200).json(data.Item);
  } catch (err) {
    res.status(500).json({ error: 'Could not retrieve team' });
  }
});

// Update a team
app.put('/teams/:name', async (req, res) => {
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

  try {
    const data = await dynamoDb.send(new UpdateCommand(params));
    res.status(200).json(data.Attributes);
  } catch (err) {
    res.status(500).json({ error: 'Could not update team' });
  }
});

// Delete a team
app.delete('/teams/:name', async (req, res) => {
  const params = {
    TableName,
    Key: {
      name: req.params.name,
    },
  };

  try {
    await dynamoDb.send(new DeleteCommand(params));
    res.status(200).json({ message: 'Team deleted successfully' });
  } catch (err) {
    res.status(500).json({ error: 'Could not delete team' });
  }
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});