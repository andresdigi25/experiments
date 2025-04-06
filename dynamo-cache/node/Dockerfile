# Use the official Node.js image from the Docker Hub
FROM node:20

# Set the working directory
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install the dependencies
RUN npm install

# Copy the Express.js application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Run the Express.js application
CMD ["node", "index.js"]