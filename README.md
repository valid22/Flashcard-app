# Flashcard-app
A Flashcard web app as part of the IITM POD MAD-1 Diploma Project. Project submitted by Vigneshwaran 21f1004210.

# Setup

The server is preset with all the configurations, but any changes required can be passed through `.env` file. 

### Python pre-requisites
You can install the python dependencies using the `requirements.txt`

```sh
pip install -r requirements.txt
```

# Usage

It's recommended to run the Flask using a WSGI app

```
gunicorn -w -b :8080 main:app
```

If guvicorn is not available, can also run for test using Flask run

```
export FLASK_APP=main.py
export FLASK_ENV=production
flask run 
```