# ckanext-spark

`ckanext-spark` provides the Data@Spark theme used by Spark!'s public CKAN
catalog at [data.buspark.io](https://data.buspark.io).

The extension changes presentation only. It does not patch CKAN core or define
custom dataset schemas, authorization rules, actions, or database tables.

## Compatibility

- CKAN 2.11 (target)
- Python 3.9–3.11

CKAN 2.11.5 is the validation target for the initial Data@Spark launch.

## Installation

Install the extension into the same environment as CKAN:

```bash
pip install -e /path/to/ckanext-spark
```

Add `spark` to `ckan.plugins` after CKAN's required plugins:

```ini
ckan.plugins = ... spark
```

Restart CKAN after installing or updating the extension.

## Development

Install the test dependency:

```bash
pip install -r dev-requirements.txt
```

Run the test suite from a configured CKAN environment:

```bash
pytest
```

The Data@Spark deployment repository supplies the reproducible CKAN container
environment used for integration and render testing.

## License

GNU Affero General Public License v3 or later. See `LICENSE`.
