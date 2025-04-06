FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Create uploads directory with proper permissions
RUN mkdir -p uploads && chmod 777 uploads

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application
CMD ["node", "server.js"]