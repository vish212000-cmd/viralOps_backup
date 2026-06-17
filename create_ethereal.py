import requests
print(requests.post('https://api.nodemailer.com/user', json={'requestor':'viralops','version':'1.0'}).text)
