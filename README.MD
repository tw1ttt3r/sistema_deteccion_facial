# Sistema Facial

## Requirements
Cmake
Python ^3.10


### Run project
- python venv env
- pip install -r requirements.txt
- create .env file and change values

- python app.py

#### Use Docker

docker run -d \
  --name mongodb-container \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=adminpassword \
  mongo

docker run -it --rm mongo mongosh "mongodb://admin:adminpassword@mongodb-container:27017"

use <database_name>
db.createCollection(<collection_name>);
db.createCollection(<collection_name>);