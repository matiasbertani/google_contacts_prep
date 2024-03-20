# Preapracion de bases de google

### To run the app from terminal
```bash
pip install -r requirements.txt 
python main.py
```

### Run with Docker
```bash
docker build -t google-contacts .
docker run -p 8050:8050 --name google-contacts google-contacts
```
