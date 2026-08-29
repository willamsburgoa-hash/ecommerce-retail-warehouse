# LinkedIn — kickoff post (draft)

---

I'm giving myself **7 days** to ship a Data Engineer portfolio. Here's the plan — and why I think a background in anthropology is an asset for this work, not a detour.

**The pitch:** fieldwork *is* data collection. Ethnography *is* qualitative analysis. I spent years turning messy, real-world observation into decisions people could act on. I'm now industrializing that instinct: reproducible pipelines that turn messy real-world data into decisions.

**Four projects, four real problems** — two in e-commerce (the problems every company recognizes), two in the cultural sector I know well:

1. **Retail analytics warehouse** — daily sales & logistics KPIs on AWS (S3 + Athena + dbt + Dagster), on the public Olist dataset.
2. **Museum collection representation** — measuring geographic/temporal/gender bias in a collection (Met API + Wikidata + dbt + Great Expectations).
3. **Clickstream lakehouse** — near-real-time product funnel on Databricks (Auto Loader + Delta medallion + dbt).
4. **Cultural-heritage media attention** — global news coverage of heritage sites (GDELT + PySpark + Delta).

**Constraints on purpose:** everything runs on free tiers / cloud credits, target cost **~$0 per project**. Small data, `terraform destroy` between sessions, a $5 budget alarm. Constraints make better engineering stories.

**Every project ships with:** a public repo, a README with an architecture diagram, green CI, a dashboard, and a short write-up of what the data actually says.

Follow along — I'll post one project per build. Feedback very welcome.

\#dataengineering #dbt #aws #databricks #analyticsengineering
