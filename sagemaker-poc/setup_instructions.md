# Address Matching Pipeline Setup Instructions

This guide will walk you through setting up a complete address matching pipeline using AWS SageMaker, Lambda, and API Gateway.

## Step 1: Train and Deploy the SageMaker Model

1. Open SageMaker in the AWS Console and create a new notebook instance
2. Once launched, create a new notebook and paste the code from `address_matching.py` into it
3. Run all cells to:
   - Create a simple address matching model
   - Package the model
   - Upload it to S3
   - Deploy it to a SageMaker endpoint
4. Note the endpoint name that was created (should be printed in the notebook output)

## Step 2: Create the Lambda Function

1. Open the Lambda service in the AWS Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Set the following:
   - Name: `address-matching-lambda`
   - Runtime: Python 3.9
   - Execution role: Create a new role with basic Lambda permissions
5. Click "Create function"
6. Replace the default code with the code from `lambda_function.py`
7. Add an environment variable:
   - Key: `SAGEMAKER_ENDPOINT_NAME`
   - Value: [Your SageMaker endpoint name from Step 1]
8. Under "Configuration" → "Permissions", click on the role name
9. In the IAM console, add the following policy to the role:
   - Select "Add permissions" → "Attach policies"
   - Search for and select "AmazonSageMakerFullAccess" (for production, use a more restrictive policy)
   - Click "Add permissions"

## Step 3: Set Up API Gateway

1. Open the API Gateway service in the AWS Console
2. Click "Create API"
3. Select "REST API" (not private) and click "Build"
4. Set the following:
   - API name: `AddressMatchingAPI`
   - Description: `API for address matching service`
   - Endpoint Type: Regional
5. Click "Create API"
6. Click "Create Resource" and set:
   - Resource Name: `match-addresses`
   - Resource Path: `/match-addresses`
   - Check "Enable API Gateway CORS"
7. Click "Create Resource"
8. With the resource selected, click "Create Method" and select "POST"
9. Configure the POST method:
   - Integration type: Lambda Function
   - Lambda Function: `address-matching-lambda`
   - Use Default Timeout: checked
10. Click "Save"
11. Click "Enable CORS" and use the default settings, then click "Enable CORS and replace existing CORS headers"
12. Click "Deploy API" and set:
    - Deployment stage: `[New Stage]`
    - Stage name: `prod`
13. Click "Deploy"
14. Note the "Invoke URL" displayed at the top of the stage editor. This is your API endpoint URL.

## Step 4: Test the API

1. Open the `test_client.html` file in a text editor
2. Host it on a local or remote web server (you can even just open it in your browser directly)
3. Enter your API URL from Step 3 in the format:
   ```
   https://{api-id}.execute-api.{region}.amazonaws.com/prod/match-addresses
   ```
4. Enter two addresses to compare
5. Click "Test Match" to see the results

## Troubleshooting

### CORS Issues
If you encounter CORS errors when testing:
1. In API Gateway, make sure CORS is enabled for your resource
2. Verify that your Lambda function includes the necessary CORS headers in the response

### Lambda Errors
If your Lambda function is failing:
1. Check CloudWatch Logs for error messages
2. Verify the environment variable for the SageMaker endpoint is correct
3. Ensure the Lambda execution role has permission to invoke the SageMaker endpoint

### SageMaker Endpoint Issues
If the SageMaker endpoint is not responding:
1. Check the endpoint status in SageMaker console
2. Review CloudWatch Logs for any model errors
3. Verify that the model artifacts were packaged correctly

## Clean Up
When you're done testing, remember to:
1. Delete the API Gateway API
2. Delete the Lambda function
3. Delete the SageMaker endpoint (to avoid ongoing charges)
4. Delete the S3 bucket contents