# Use the official Node.js 18 Alpine image as the base image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install ALL dependencies (including dev dependencies for build)
RUN npm ci

# Copy the rest of the application code
COPY . .

# Copy environment file
COPY .env.local .env.local

# Build the Next.js application
RUN npm run build

# Remove dev dependencies to reduce image size
RUN npm prune --production

# Expose the port that the Next.js app will run on
EXPOSE 8302

# Set environment variable for production
ENV NODE_ENV=production
ENV PORT=8302

# Start the Next.js application
CMD ["npm", "start"]
