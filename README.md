# mockapi

Mock HTTP API server configured with a single JSON file. Useful to work on a frontend
or a client before the real backend exists, or to reproduce errors and slow responses.

## Install

```
git clone <repo-url> mockapi
cd mockapi
```

Requires Python 3.11+, no third-party dependencies.

## Usage

```
python main.py examples/api.json --check
python main.py examples/api.json -p 8080 --cors
python main.py examples/api.json --watch
```

```
curl localhost:8080/users/7?lang=fr
curl -X POST localhost:8080/echo/test -d '{"a": 1}'
```

## Docker

```
docker build -t mockapi .
docker run --rm -p 8080:8080 mockapi
```

To serve your own routes, mount the directory holding the config file:

```
docker run --rm -p 8080:8080 -v "$PWD/mocks:/mocks:ro" mockapi /mocks/api.json --host 0.0.0.0 --watch
```

## Routes

Routes are listed under `"routes"` in the config file. See `examples/api.json`.

| Field | Default | Description |
|---|---|---|
| `method` | `GET` | HTTP method |
| `path` | | `/users/{id}` for a parameter, `/static/*` for a prefix |
| `status` | `200` | status code |
| `body` | `null` | JSON value or string, `{{params.x}}` and `{{query.x}}` are substituted |
| `body_file` | | file to serve, relative to the config file |
| `headers` | `{}` | extra response headers |
| `delay_ms` | `0` | wait before responding |
| `echo` | `false` | return the received request as JSON |
| `fail_rate` | `0` | probability (0 to 1) of answering with a 500 error instead |

Headers set in the top-level `"headers"` object are added to every response.

With `--watch`, the file is reloaded on the first request after it changes. If the new
version is invalid, the error is printed and the previous routes keep being served.
