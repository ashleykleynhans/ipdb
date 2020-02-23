## Requirements

* Docker (https://www.docker.com/community-edition#/download)
* Docker Compose (https://docs.docker.com/compose/)

## Installation

1. Clone the repo

        git clone https://github.com/ashleykleynhans/ipdb.git

2. Change directory to the folder where you cloned the repo to, then change directory to the docker subdirectory

        cd ipdb
        cd docker
        
3. Create a Docker .env file:

        cp .env.example .env
        
4. Edit the .env file and set the path to the API_VOLUME, DB_VOLUME, and set the credentials for the database. Most of the code uses URI schema to connect to the database, so avoid characters that usually form part of URI strings, such as #, %, etc.

5. Start the Docker containers, which will download and install all the required software

        docker-compose up -d

6. Create a .env file

        docker-compose exec ip-api cp .env.example .env

7. Configure the database connection, edit the .env file and set the following under the [database] section (these credentials must obviously match the ones you specified in point (4) above):

        DB_USER=ipdb
        DB_PASS=password
        DB_HOST=ip-db
        DB_NAME=ipdb
        
8. Configure the API credentials, edit the .env file and set the following under the [api] section:

        API_USER=ansible
        API_PASS=password
        
9. Create the DB migration config file:

        docker compose exec ip-api python setup.py
        
10. Apply the DB migrations:

        docker-compose exec ip-api yoyo apply

11. Optionally import your hosts file into the database - this must be run **locally** and **NOT** within the Docker container.

        python scripts/import_hosts.py

12. The App listens for incoming connections at http://127.0.0.1 (on port 8000, assuming that port 8000 is not already in use)

13. Generate a JWT access token (this will be appended to each API endpoint as ?access_token=xxxxxx):

        docker-compose exec ip-api python create_token.py

14. See the [Postman Collection](IP API.postman_collection.json).
