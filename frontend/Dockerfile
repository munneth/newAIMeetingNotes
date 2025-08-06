FROM node:18

WORKDIR /app

# Copy only package files first (for caching)
COPY meeting-mash/package*.json ./
RUN npm install

# Copy the actual Next.js project
COPY meeting-mash/ .

EXPOSE 3000

# Enable host access for hot reload
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]

