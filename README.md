# Train journey recorder

Get the details of trains you've been on, and present them prettily

## Dependencies

You can install the packages yourself with `pip`...

```sh
pip install Jinja2 termcolor libsass
```

... or use the `requirements.txt` file...

```sh
pip install -r requirements.txt
```

...or use `pipenv`.

```sh
pipenv install
```

## Credentials

You will need to provide your credentials for the various APIs at work.

### Realtime Trains

You will need an API username and password, which can be found at the [Realtime Trains API page](https://api.rtt.io/).
Place your credentials in an `rtt.credentials` file in the project root in the following format.

```sh
username
password
```
