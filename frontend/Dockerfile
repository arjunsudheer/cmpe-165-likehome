FROM node:20-alpine

WORKDIR /app

# Install deps separately for layer caching
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host binds Vite to 0.0.0.0 so it is reachable outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]