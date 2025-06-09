## Getting Started (Docker)

### Prerequisites
- **Docker** (https://docs.docker.com/get-docker/)
- **Docker Compose** (https://docs.docker.com/compose/)

### Configuration
1. **Clone the repository:**
   ```sh
   git clone https://github.com/riceowls256/Hist_Data_Ingestor.git
   cd Hist_Data_Ingestor
   ```
2. **Set up environment variables:**
   - Copy the example file and fill in your secrets:
     ```sh
     cp .env.example .env
     ```
   - Edit `.env` with your API keys and database credentials.

### Running the Application
```sh
docker-compose up --build -d
```
- The app will be available on port 8000 (or as configured).
- TimescaleDB will be available on port 5432.

### Using the CLI
To run a CLI command inside the app container:
```sh
docker-compose exec app python -m src.cli ingest --api databento
```

### Stopping the Environment
To stop and remove all containers:
```sh
docker-compose down
```

### (Optional) pgAdmin
- To enable pgAdmin, uncomment the `pgadmin` service in `docker-compose.yml` and set the credentials in `.env`.
- Access pgAdmin at [http://localhost:5050](http://localhost:5050). 