// Lambda function to fetch logs from two different microservices
const AWS = require('aws-sdk');
const cloudwatchlogs = new AWS.CloudWatchLogs();

exports.handler = async (event, context) => {
    try {
        // Extract query parameters (with defaults)
        const queryParams = event.queryStringParameters || {};
        
        // Set time range for the query (default: last 24 hours)
        const endTime = new Date().getTime();
        const startTime = queryParams.startTime 
            ? new Date(queryParams.startTime).getTime() 
            : endTime - (24 * 60 * 60 * 1000);
            
        // Log group names for the two microservices
        const service1LogGroup = '/aws/lambda/microservice1';
        const service2LogGroup = '/aws/lambda/microservice2';
        
        // Filter pattern (empty string means "match everything")
        const filterPattern = queryParams.filterPattern || '';
        
        // Get logs from both services
        const [service1Logs, service2Logs] = await Promise.all([
            queryLogsFromLogGroup(service1LogGroup, startTime, endTime, filterPattern),
            queryLogsFromLogGroup(service2LogGroup, startTime, endTime, filterPattern)
        ]);
        
        // Process and format the log data for Power BI consumption
        const formattedLogs = formatLogsForPowerBI(service1Logs, service2Logs);
        
        // Return the response
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formattedLogs)
        };
    } catch (error) {
        console.error('Error fetching logs:', error);
        
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ error: 'Failed to fetch logs', details: error.message })
        };
    }
};

// Function to query logs from a specific log group
async function queryLogsFromLogGroup(logGroupName, startTime, endTime, filterPattern) {
    // Use CloudWatch Logs Insights query for more powerful filtering
    const query = `
        fields @timestamp, @message
        | filter @message like /${filterPattern}/
        | sort @timestamp desc
        | limit 1000
    `;
    
    // Start the query
    const startQueryResponse = await cloudwatchlogs.startQuery({
        logGroupName: logGroupName,
        startTime: Math.floor(startTime / 1000),  // Convert to seconds
        endTime: Math.floor(endTime / 1000),      // Convert to seconds
        queryString: query
    }).promise();
    
    // Get the query ID
    const queryId = startQueryResponse.queryId;
    
    // Poll for results
    let queryResults;
    let queryStatus;
    
    do {
        // Wait a bit before checking again
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Get the current results
        const queryResponse = await cloudwatchlogs.getQueryResults({
            queryId: queryId
        }).promise();
        
        queryResults = queryResponse.results;
        queryStatus = queryResponse.status;
        
    } while (queryStatus === 'Running');
    
    // Process results
    return {
        logGroupName,
        status: queryStatus,
        results: queryResults
    };
}

// Format logs in a structure that's easy for Power BI to consume
function formatLogsForPowerBI(service1Logs, service2Logs) {
    const formattedLogs = [];
    
    // Process logs from service 1
    if (service1Logs.results && service1Logs.results.length > 0) {
        service1Logs.results.forEach(logEvent => {
            const timestampField = logEvent.find(field => field.field === '@timestamp');
            const messageField = logEvent.find(field => field.field === '@message');
            
            if (timestampField && messageField) {
                try {
                    // Try to parse JSON messages
                    let messageObj;
                    try {
                        messageObj = JSON.parse(messageField.value);
                    } catch (e) {
                        messageObj = { rawMessage: messageField.value };
                    }
                    
                    formattedLogs.push({
                        timestamp: new Date(timestampField.value).toISOString(),
                        service: 'microservice1',
                        ...messageObj
                    });
                } catch (e) {
                    console.error('Error parsing log entry:', e);
                }
            }
        });
    }
    
    // Process logs from service 2
    if (service2Logs.results && service2Logs.results.length > 0) {
        service2Logs.results.forEach(logEvent => {
            const timestampField = logEvent.find(field => field.field === '@timestamp');
            const messageField = logEvent.find(field => field.field === '@message');
            
            if (timestampField && messageField) {
                try {
                    // Try to parse JSON messages
                    let messageObj;
                    try {
                        messageObj = JSON.parse(messageField.value);
                    } catch (e) {
                        messageObj = { rawMessage: messageField.value };
                    }
                    
                    formattedLogs.push({
                        timestamp: new Date(timestampField.value).toISOString(),
                        service: 'microservice2',
                        ...messageObj
                    });
                } catch (e) {
                    console.error('Error parsing log entry:', e);
                }
            }
        });
    }
    
    return {
        count: formattedLogs.length,
        logs: formattedLogs
    };
}