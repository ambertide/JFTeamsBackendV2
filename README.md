# JotForm Polls for Microsoft Teams Proxy

[![Read the API Documentation](https://img.shields.io/badge/docs-Read%20the%20API%20Documentation-blue)](https://ambertide-jfteams-proxy.herokuapp.com/docs)

This is a proxy server written in Python's FastAPI to fulfill the following requirements:

1. Act as a proxy server that can store user credentials on a Redis cache as a KV pair where
   the key is a UUID, using this UUID, act as a proxy of some JotForm endpoints.
2. Act to calculate the distributions of submissions to certain forms.

## Installation

You will need Python 3.9 for this project, and prefably a Unix environment, below
commands are for bash:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To start the development server:

```
uvicorn main:app
```
