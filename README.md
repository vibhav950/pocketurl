# PocketURL

A service that shortens arbitrary-length URLs down to brief 8-character paths on the `pocketurl.com` domain.

## Setup

```zsh
git clone https://github.com/vibhav950/pocketurl.git
```

Refer to [kubernetes/README.md](kubernetes/README.md)

## To shorten a URL

Assuming the service is bound to `localhost:5000`

```zsh
curl -X POST http://localhost:5000/shorten \                                                              
     -H "Content-Type: application/json" \
     -d '{"url": "https://google.com"}'
```

Voila! You can now make a GET request to the shortened URL you got in the response body, and you will automatically be redirected to the original URL

```zsh
curl -X GET "http://localhost:5000/<short_url>"
```
