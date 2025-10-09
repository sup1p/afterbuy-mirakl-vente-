# Docker Instructions for Extrup Admin Frontend

## Build and Run

### Build the Docker image
```bash
docker build -t extrup-admin .
```

### Run the container
```bash
docker run -p 3000:3000 extrup-admin
```

The application will be available at `http://localhost:8180` (via nginx)

## Environment Configuration

The `.env.local` file is included in the Docker image with the following configuration:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8180
```

### Connecting to Backend

If your backend is running on a different host/port, you can override the environment variable:

```bash
docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE_URL=http://your-backend-host:8180 extrup-admin
```

Or if using Docker Compose with nginx service:
```bash
docker run -p 3000:3000 --network your-network -e NEXT_PUBLIC_API_BASE_URL=http://nginx:80 extrup-admin
```

## Development

For development with hot reload, use:
```bash
npm run dev
```

## Production Deployment

The Docker image is optimized for production with:
- Multi-stage build (if needed in future)
- Production Node.js environment
- Optimized Next.js build
- Minimal Alpine Linux base image