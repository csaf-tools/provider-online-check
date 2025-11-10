# CSAF Provider Scan Frontend

Vue.js frontend application with Bootstrap for the CSAF Provider Scan.

## Setup

If not using Docker:

```bash
npm install
```

## Running the Application

### Development
```bash
npm run dev
```

The application will be available at http://localhost:8080

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Docker

The application is configured to run in development mode with hot-reloading enabled.

```bash
docker compose up -d
# or man
docker build -t scan-frontend .
docker run -p 5173:5173 -v $(pwd):/app scan-frontend
```
