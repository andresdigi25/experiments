const express = require('express');
const { DynamoDBClient, CreateTableCommand, PutItemCommand, GetItemCommand, UpdateTimeToLiveCommand } = require('@aws-sdk/client-dynamodb');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

const dynamoDBClient = new DynamoDBClient({
  endpoint: process.env.DYNAMODB_ENDPOINT,
  region: 'us-east-1',
  credentials: {
    accessKeyId: 'dummy',
    secretAccessKey: 'dummy'
  }
});

const createTable = async () => {
  const params = {
    TableName: 'Cache',
    KeySchema: [
      { AttributeName: 'key', KeyType: 'HASH' }
    ],
    AttributeDefinitions: [
      { AttributeName: 'key', AttributeType: 'S' }
    ],
    ProvisionedThroughput: {
      ReadCapacityUnits: 10,
      WriteCapacityUnits: 10
    }
  };

  try {
    await dynamoDBClient.send(new CreateTableCommand(params));
    await dynamoDBClient.send(new UpdateTimeToLiveCommand({
      TableName: 'Cache',
      TimeToLiveSpecification: {
        Enabled: true,
        AttributeName: 'ttl'
      }
    }));
  } catch (error) {
    if (error.name !== 'ResourceInUseException') {
      console.error('Error creating table:', error);
    }
  }
};

createTable();

app.post('/cache', async (req, res) => {
  const { key, value, ttl } = req.body;
  const ttlTimestamp = Math.floor(Date.now() / 1000) + ttl;
  const params = {
    TableName: 'Cache',
    Item: {
      'key': { S: key },
      'value': { S: value },
      'ttl': { N: ttlTimestamp.toString() }
    }
  };

  try {
    await dynamoDBClient.send(new PutItemCommand(params));
    res.json({ message: 'Item cached' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/cache/:key', async (req, res) => {
  const { key } = req.params;
  const params = {
    TableName: 'Cache',
    Key: {
      'key': { S: key }
    }
  };

  try {
    const data = await dynamoDBClient.send(new GetItemCommand(params));
    if (data.Item) {
      res.json({ key: data.Item.key.S, value: data.Item.value.S });
    } else {
      res.status(404).json({ message: 'Item not found' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Server is running on port 3000');
});