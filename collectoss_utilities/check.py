import re
import sys
import logging
import click


# Matches https://github.com/<owner>/<repo>  (optional .git suffix, optional trailing slash)
_GITHUB_HTTPS_RE = re.compile(
    r'^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$',
    re.IGNORECASE,
)


def is_valid_github_url(url: str) -> bool:
    """Return True if *url* looks like a valid GitHub HTTPS repository URL."""
    return bool(_GITHUB_HTTPS_RE.match(url.strip()))


def _url_variants(url: str) -> set:
    """Return the common storage variants for a URL.

    The database may store URLs with or without a trailing ``.git`` or a
    trailing slash, so we generate all four combinations and use them in an
    ``IN`` query rather than relying on the caller to normalise first.
    """
    url = url.strip().rstrip('/')
    base = url[:-4] if url.endswith('.git') else url
    return {base, base + '/', base + '.git', base + '.git/'}


def _check_repos_in_db(urls: list) -> list:
    """Query the database for each URL and return results.

    Returns:
        List of ``(url, found: bool, repo_id: int | None)`` tuples in the
        same order as *urls*.
    """
    from collectoss.application.db.models import Repo
    from collectoss.application.db.session import DatabaseSession

    logger = logging.getLogger(__name__)
    results = []

    with DatabaseSession(logger) as session:
        for url in urls:
            candidates = _url_variants(url)
            repo = session.query(Repo).filter(Repo.repo_git.in_(candidates)).first()
            if repo:
                results.append((url, True, repo.repo_id))
            else:
                results.append((url, False, None))

    return results


def _collect_urls(raw_urls: tuple, url_file) -> list:
    """Gather URLs from CLI positional arguments and/or a file.

    Lines that are empty or start with ``#`` are ignored when reading from a
    file.
    """
    urls = list(raw_urls)
    if url_file:
        for line in url_file:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls


@click.command(name="check-repos")
@click.argument('urls', nargs=-1)
@click.option(
    "-f", "--file",
    "url_file",
    type=click.File('r'),
    required=False,
    default=None,
    help="File containing one GitHub repo URL per line (# lines are ignored).",
)
def command(urls, url_file):
    """Check whether GitHub repos are present in the CollectOSS database.

    URLs may be supplied directly as arguments, read from a file with
    --file, or both.  Each URL must be a valid GitHub HTTPS repository URL
    (e.g. https://github.com/owner/repo).

    Exits with status 1 if any repos are not found in the database.
    """
    all_urls = _collect_urls(urls, url_file)

    if not all_urls:
        raise click.UsageError(
            "Provide at least one URL as an argument or via --file / -f."
        )

    # ── Validation ──────────────────────────────────────────────────────────
    invalid = [u for u in all_urls if not is_valid_github_url(u)]
    if invalid:
        for u in invalid:
            click.echo(
                click.style("  INVALID  ", fg="yellow", bold=True) + f" {u}",
                err=True,
            )
        raise click.UsageError(
            f"{len(invalid)} URL(s) failed GitHub HTTPS URL validation (listed above)."
        )

    # ── Database lookup ──────────────────────────────────────────────────────
    try:
        results = _check_repos_in_db(all_urls)
    except Exception as exc:
        raise click.ClickException(f"Database error: {exc}") from exc

    found_count = 0
    missing_count = 0
    for url, found, repo_id in results:
        if found:
            found_count += 1
            click.echo(
                click.style("  FOUND    ", fg="green", bold=True)
                + f" {url}  (repo_id={repo_id})"
            )
        else:
            missing_count += 1
            click.echo(
                click.style("  MISSING  ", fg="red", bold=True) + f" {url}"
            )

    click.echo("")
    click.echo(
        f"Summary: {found_count} found, {missing_count} missing"
        f" out of {len(results)} checked."
    )

    if missing_count:
        sys.exit(1)
