"""
GitHub Repository Insights Extractor — Apify Actor

Extracts structured data about GitHub repositories: stars, forks, contributors,
release info, language breakdown, README analysis, and community health metrics.
Uses the public GitHub REST API.
"""
import asyncio
import logging
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
import json

from apify import Actor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def github_request(endpoint: str, token: str = "") -> dict[str, Any]:
    """Make an unauthenticated GitHub API request."""
    url = f"{GITHUB_API}{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "apify-github-insights/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        logger.warning("GitHub API %s returned %s", endpoint, e.code)
        return {}
    except Exception as e:
        logger.warning("GitHub API error for %s: %s", endpoint, e)
        return {}


async def fetch_repo_insights(owner: str, repo: str, token: str) -> dict[str, Any]:
    """Fetch all available insights for a single repository."""

    def _fetch():
        result = {
            "type": "repo_insights",
            "full_name": f"{owner}/{repo}",
        }

        # 1. Basic repo info
        repo_data = github_request(f"/repos/{owner}/{repo}", token)
        if not repo_data:
            return None

        result.update({
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "homepage": repo_data.get("homepage"),
            "language": repo_data.get("language"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "open_issues": repo_data.get("open_issues_count"),
            "watchers": repo_data.get("watchers_count"),
            "default_branch": repo_data.get("default_branch"),
            "license": (repo_data.get("license") or {}).get("spdx_id"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "size_kb": repo_data.get("size"),
            "archived": repo_data.get("archived", False),
            "topics": repo_data.get("topics", []),
        })

        # 2. Language breakdown
        lang_data = github_request(f"/repos/{owner}/{repo}/languages", token)
        if lang_data:
            total = sum(lang_data.values()) or 1
            result["languages"] = {
                lang: {"bytes": bytes_, "percentage": round(bytes_ / total * 100, 2)}
                for lang, bytes_ in lang_data.items()
            }

        # 3. Latest release
        release_data = github_request(f"/repos/{owner}/{repo}/releases/latest", token)
        if release_data:
            result["latest_release"] = {
                "tag": release_data.get("tag_name"),
                "name": release_data.get("name"),
                "published_at": release_data.get("published_at"),
                "prerelease": release_data.get("prerelease", False),
                "downloads": sum(
                    a.get("download_count", 0)
                    for a in release_data.get("assets", [])
                ),
            }

        # 4. Community health
        community_data = github_request(
            f"/repos/{owner}/{repo}/community/profile", token
        )
        if community_data:
            result["community"] = {
                "health_percentage": community_data.get("health_percentage"),
                "has_readme": bool(community_data.get("files", {}).get("readme")),
                "has_contributing": bool(community_data.get("files", {}).get("contributing")),
                "has_license": bool(community_data.get("files", {}).get("license")),
                "has_code_of_conduct": bool(community_data.get("files", {}).get("code_of_conduct")),
                "has_issue_template": bool(community_data.get("files", {}).get("issue_template")),
                "has_pr_template": bool(community_data.get("files", {}).get("pull_request_template")),
            }

        # 5. Contributor count (approximate via contributors endpoint)
        contrib_data = github_request(
            f"/repos/{owner}/{repo}/contributors?per_page=1&anon=true", token
        )
        if isinstance(contrib_data, list) and contrib_data:
            result["contributors_count_approx"] = len(contrib_data)

        return result

    return await asyncio.get_event_loop().run_in_executor(None, _fetch)


async def main() -> None:
    """Main actor entry point."""
    async with Actor:
        actor_input = await Actor.get_input() or {}

        repos_input: list[str] = actor_input.get("repos", [])
        github_token: str = actor_input.get("githubToken", "")

        if not repos_input:
            logger.warning("No repos provided in input. Add 'repos' array with 'owner/repo' strings.")
            return

        logger.info("Processing %d repositories...", len(repos_input))

        # Process with concurrency limit of 3 (unauthenticated rate limit friendly)
        semaphore = asyncio.Semaphore(3)

        async def process_repo(repo_full: str):
            async with semaphore:
                parts = repo_full.strip().split("/")
                if len(parts) != 2:
                    logger.warning("Invalid repo format: %s (expected owner/repo)", repo_full)
                    return
                owner, repo = parts
                logger.info("Fetching insights for %s/%s...", owner, repo)
                data = await fetch_repo_insights(owner, repo, github_token)
                if data:
                    await Actor.push_data(data)
                    logger.info("  -> %s: %d stars, %d forks, language=%s",
                        data["full_name"], data.get("stars", 0),
                        data.get("forks", 0), data.get("language", "?"),
                    )

        tasks = [process_repo(r) for r in repos_input]
        await asyncio.gather(*tasks)
        logger.info("Done! All repositories processed.")


if __name__ == "__main__":
    asyncio.run(main())
