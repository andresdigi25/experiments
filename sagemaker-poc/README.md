# Address Matching in Docker

This repository contains everything needed to run the address matching model locally in Docker, either as a Python script or as a Jupyter notebook.

## Prerequisites

- Docker installed on your machine
- AWS credentials (if you plan to deploy to SageMaker)
- The `address_matching.py` file in this directory

## File Structure

```
address-matching/
├── address_matching.py     # Your address matching code
├── requirements.txt        # Python dependencies
├── Dockerfile              # For running as a Python script
├── Dockerfile.jupyter      # For running in Jupyter notebook
├── run.sh                  # Script to run with standard Docker
└── run_jupyter.sh          # Script to run with Jupyter
```

## Option 1: Run as Python Script

This option runs the address matching code directly in a Docker container.

1. Make the run script executable:
```bash
chmod +x run.sh
```

2. Run the script:
```bash
./run.sh
```

The script will:
- Build a Docker image with all required dependencies
- Run the container with your AWS credentials
- Save any outputs to the `output` directory

## Option 2: Run in Jupyter Notebook

This option starts a Jupyter notebook server in a Docker container, allowing you to interactively work with the code.

1. Make the Jupyter run script executable:
```bash
chmod +x run_jupyter.sh
```

2. Run the script:
```bash
./run_jupyter.sh
```

3. Open your browser and navigate to:
```
http://localhost:8888
```

4. You'll find your address matching notebook ready to use

## AWS Credentials

Both scripts will automatically use AWS credentials from your environment. If you have the AWS CLI configured, it will use those credentials.

Alternatively, you can set these environment variables before running the scripts:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"  # Change to your preferred region
```

## Customizing the Run

If you need to modify the default behavior:

1. **Change Port**: Edit the `-p 8888:8888` in run_jupyter.sh to use a different port
2. **Add More Volumes**: Add more `-v` options to mount additional directories
3. **Change Region**: Set the `AWS_REGION` environment variable

## Troubleshooting

### Docker Issues
- Make sure Docker daemon is running
- Try running `docker info` to verify Docker is working correctly

### Permission Issues
- If you encounter permission problems, make sure the run scripts are executable

### AWS Connection Issues
- Verify your AWS credentials are correct
- Check that your IAM user has permissions for SageMaker

## Deploying to SageMaker

After you've validated the model works locally, you can deploy it to SageMaker by:

1. Following the code in the `address_matching.py` file to upload and deploy
2. Using the AWS Management Console to create a notebook instance and upload this code
3. Following the instructions in the SageMaker deployment guide

## Clean Up

To clean up Docker resources:

```bash
# Remove the Docker images
docker rmi address-matching address-matching-jupyter

# Remove any stopped containers
docker container prune
```