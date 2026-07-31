import requests
from bs4 import BeautifulSoup
import re

# We need to login first
session = requests.Session()
login_url = "http://127.0.0.1:8000/login/"
resp = session.get(login_url)
soup = BeautifulSoup(resp.content, "html.parser")
csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

login_data = {
    "csrfmiddlewaretoken": csrf_token,
    "username": "Adamelmir",
    "password": "password" # I don't know the password... Wait, let's just use Django test client.
}
