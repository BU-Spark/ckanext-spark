# ckanext-spark

`ckanext-spark` provides the Data@Spark theme used by Spark!'s public CKAN
catalog at [data.buspark.io](https://data.buspark.io).

The extension is presentation plus the topic taxonomy. It does not patch CKAN
core or define custom dataset schemas, authorization rules, actions, or database
tables; the one thing it writes is the fixed set of topic groups, via the
`spark init-topics` command below.

## Topics

Datasets are categorised with a fixed, rolled-up taxonomy of 11 subject areas
(the "academic disciplines" list, not the detailed 40–50 item breakdown — CKAN's
topic model is flat, so only the top level is representable). The list is
defined in `ckanext/spark/topics.py` and is kept identical to `SPARK_TOPICS` in
the Atlas project gallery, so a dataset and a project describe themselves with
the same words.

Topics are CKAN **groups** rather than free tags. Groups are flat, so they fit
the same constraint tags would, but unlike tags they are a controlled vocabulary
(no typos, no near-duplicates), they get a browsable page each, and CKAN already
facets search on them.

Assigning a topic is a **second step after creating a dataset**: CKAN 2.11's
dataset form has an Organization selector but no group selector, so a topic is
set from the dataset's *Groups* tab (`/dataset/groups/<name>`) or by adding the
dataset from the topic's own page. Worth knowing, because it means a dataset can
be created with no topic at all and nothing will complain. Putting an 11-way
topic picker directly on the dataset form is the obvious follow-up if datasets
start landing untagged.

Create the topic groups on a new site (safe to re-run; it repairs a wrong title
or a soft-deleted topic and leaves descriptions and images alone):

```bash
ckan -c /etc/ckan/default/ckan.ini spark init-topics
```

The unrelated `featured` **tag** still flags datasets for the homepage's
Featured tab. That's a flag, not a topic.

## Compatibility

- CKAN 2.11 (target)
- Python 3.10–3.14

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

`docker-compose.dev.yml` runs a complete local CKAN 2.11 with the repo
bind-mounted, so template and CSS edits appear on reload:

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml exec ckan \
    ckan -c "$CKAN_INI" spark init-topics
open http://localhost:5000        # sign in as ckan_admin / test1234
```

Run the tests inside that container, which is the only place CKAN itself is
importable:

```bash
docker compose -f docker-compose.dev.yml exec ckan \
    pytest --ckan-ini=test.ini ckanext/spark/tests
```

This stack is for local work only — the credentials in it are fixed test values
and it serves plain HTTP on localhost. It is deliberately separate from
`infra-public-data-portal`, whose compose is a half-finished Kubernetes
migration still pinned to CKAN 2.10 and Solr 8 (Solr 8 cannot serve a 2.11
schema).

## Deployment

**Making a skin or taxonomy change here does not, by itself, deploy anything.**
The live Data@Spark image is built by `BU-Spark/ckan-docker`
(`data-at-spark/Dockerfile`), which installs this extension from an exact,
hardcoded Git commit:

```dockerfile
ARG CKANEXT_SPARK_COMMIT=<some commit sha>
```

That pin is deliberate, not an oversight — the same reasoning `ckan-docker`
uses for its other pinned dependencies applies here: a branch name is not a
pin, and a floating reference would mean some *other*, unrelated change could
silently drag in unreviewed theme code with no corresponding change in
`ckan-docker`'s own history.

So after merging a PR here, someone has to go update that pin by hand:

1. In `ckan-docker`, update `CKANEXT_SPARK_COMMIT` in both
   `data-at-spark/Dockerfile` and the default in `data-at-spark/compose.yml`
   to this repo's new `main` commit SHA.
2. Push that change to `ckan-docker`'s `master` — that push is what actually
   triggers the build, publish, and (for `int`) automatic redeploy. Merging
   here does not.

See `ckan-docker`'s `data-at-spark/README.md` for the full procedure.

## License

GNU Affero General Public License v3 or later. See `LICENSE`.
