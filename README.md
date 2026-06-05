# GitHub Repository Insights Extractor

Extract comprehensive, structured data about any public GitHub repository. Built for investors, recruiters, researchers, and developer tool builders who need programmatic access to repository analytics.

## What You Get

For each repository, this actor extracts:

| Category | Fields |
|----------|--------|
| **Basic Info** | Full name, description, homepage, language, license, topics |
| **Popularity** | Stars, forks, watchers, open issues count |
| **Activity** | Created, updated, pushed timestamps |
| **Languages** | Full language breakdown with byte count and percentages |
| **Releases** | Latest release tag, name, date, download count, prerelease flag |
| **Community** | Health score, has README/CONTRIBUTING/LICENSE/CoC/templates |
| **Size** | Repository size in KB |

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repos` | string[] | Yes | List of repos as `owner/repo` (e.g. `facebook/react`) |
| `githubToken` | string | No | GitHub PAT for 5000 req/hr rate limit |

## Example Input

```json
{
  "repos": ["apify/apify-sdk-python", "facebook/react", "microsoft/vscode"],
  "githubToken": ""
}
```

## Output Format

Each repository produces one dataset record with all fields. Perfect for exporting to CSV/JSON for analysis in Excel, Pandas, or BI tools.

## Use Cases

- **Tech Due Diligence**: Assess open-source project health before depending on it
- **Competitive Analysis**: Track competitor repos — stars, releases, community engagement
- **Investor Research**: Evaluate startup tech stacks and developer ecosystem
- **Recruiting**: Find active projects in specific tech stacks
- **Academic Research**: Study open-source trends at scale

## Pricing

Pay-per-event: 1 event per repository processed.

## Rate Limits

- Without token: ~60 repos/hour
- With token: ~5,000 repos/hour

---

**Built with Apify SDK for Python**
