# Stage 1: Build Next.js app
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies first (leverages caching)
COPY package*.json ./
RUN npm ci

# Copy configuration and source code
COPY tsconfig.json ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY next.config.js ./
COPY src/ ./src

# Set build-time env variable
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the app
RUN npm run build

# Stage 2: Production image
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built package and node_modules for server execution
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next

# Expose Next.js port
EXPOSE 3000

# Start server
CMD ["npm", "run", "start"]
