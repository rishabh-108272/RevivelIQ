# Build stage
FROM node:23-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built static files to Nginx serve directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx configuration file for custom routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
