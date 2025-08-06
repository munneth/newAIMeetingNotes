FROM node:18

# Set work directory
WORKDIR /app

# Install dependencies first (cache layer)
COPY package*.json ./
RUN npm install

# Copy the rest of the code
COPY . .

# Expose backend port
EXPOSE 5000

# Start the backend
CMD ["node", "server.js"]
