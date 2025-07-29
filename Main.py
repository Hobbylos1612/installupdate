import requests
webhook_url = "https://discord.com/api/webhooks/1350538017751830640/WFLLCXiS97voaDbuHnbVAxdVwCfzU5XkHL7_6aVJdlccMijBte8gAC5oiA4aX6MTxXbM"
requests.post(webhook_url, json={"content": "Test234"})
