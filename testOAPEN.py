# Test the OAPEN endpoint manually first:
import requests
response = requests.get("https://library.oapen.org/oai?verb=Identify")
print(response.status_code)  # Should be 200
print(response.text)  # Check for XML response