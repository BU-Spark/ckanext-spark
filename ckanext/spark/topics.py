"""The Data@Spark topic taxonomy.

This is the rolled-up ("academic disciplines") list of ~11 categories, NOT the
detailed 40-50 item breakdown. CKAN's topic model is flat, so only the top level
is representable -- the detailed list would need a hierarchy CKAN doesn't have.

Kept deliberately identical to `SPARK_TOPICS` in the Atlas project gallery
(spark-portfolio/hub/lib/data.ts) so a dataset and a project describe themselves
with the same words. If that list changes, change this one in the same PR.

Topics are modelled as CKAN *groups*, not free tags: groups are flat (so they
fit the constraint), but unlike tags they are a controlled vocabulary, they get
a browsable page each, and CKAN already facets search on them. The `featured`
tag is unrelated -- that's a flag, not a topic.

Each entry is (name, title). `name` is the CKAN group name: it is the URL
(/group/<name>) and the key datasets are joined on, so it is written down
explicitly rather than derived from the title. Deriving it would mean that
retitling a topic silently changes its URL and orphans every dataset filed
under the old one. Retitle freely; never edit a `name`.
"""

SPARK_TOPICS = [
    ("housing-urban-development", "Housing & Urban Development"),
    ("government-politics-public-policy", "Government, Politics & Public Policy"),
    ("criminal-justice-public-safety", "Criminal Justice & Public Safety"),
    ("education-learning", "Education & Learning"),
    ("immigration-community-social-services", "Immigration, Community & Social Services"),
    ("business-economy-work", "Business, Economy & Work"),
    ("health-medicine-wellbeing", "Health, Medicine & Wellbeing"),
    ("environment-sustainability", "Environment & Sustainability"),
    ("law-civil-rights", "Law & Civil Rights"),
    ("media-technology-communication", "Media, Technology & Communication"),
    ("arts-culture-humanities", "Arts, Culture & Humanities"),
]

# name -> title, for turning a search facet (which reports group names) back
# into something displayable.
TITLES = dict(SPARK_TOPICS)
