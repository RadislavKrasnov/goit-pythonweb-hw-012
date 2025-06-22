# Project installation  
1. clone the repository on your local machine https://github.com/RadislavKrasnov/goit-pythonweb-hw-012.git  
2. [install Docker](https://docs.docker.com/engine/install/)
3. [install Dockder Compose](https://docs.docker.com/compose/install/)
4. Start the API server. Go to the project folder and run the following command in CLI  
```
docker compose up
```
# Run tests  
Run unit and integration tests  
```
docker compose exec app pytest tests
```  
The coverage can be found by the following path  `htmlcov/index.html`

# API documentation  
Swagger API documentation http://localhost:8000/docs  
Sphinx API documentation http://localhost:8000/docs-html/  
