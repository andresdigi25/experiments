# Stage 1: Build the Angular application
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build --lsprod

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

COPY --from=build /app/dist/my-angular-app /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]