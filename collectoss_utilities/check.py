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


def _write_report(output_path: str, found: list, missing: list, invalid: list) -> None:
    """Write a plain-text grouped report to *output_path*."""
    lines = []

    if invalid:
        lines.append(f"=== INVALID ({len(invalid)}) ===")
        for url in invalid:
            lines.append(f"  {url}")
        lines.append("")

    lines.append(f"=== FOUND ({len(found)}) ===")
    for url, repo_id in found:
        lines.append(f"  {url}  (repo_id={repo_id})")
    lines.append("")

    lines.append(f"=== MISSING ({len(missing)}) ===")
    for url in missing:
        lines.append(f"  {url}")
    lines.append("")

    total_valid = len(found) + len(missing)
    lines.append(
        f"Summary: {len(found)} found, {len(missing)} missing"
        f" out of {total_valid} valid URLs checked"
        + (f", {len(invalid)} invalid" if invalid else "")
        + "."
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


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
@click.option(
    "-o", "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True),
    required=False,
    default=None,
    help="Write results to this file instead of stdout.",
)
def command(urls, url_file, output_path):
    """Check whether GitHub repos are present in the CollectOSS database.

    URLs may be supplied directly as arguments, read from a file with
    --file/-f, or both.  Each URL must be a valid GitHub HTTPS repository URL
    (e.g. https://github.com/owner/repo).

    Results are grouped: invalid URLs are reported first (to stderr), then
    found repos, then missing repos.  Use --output/-o to write the report to
    a file instead of stdout.

    Exits with status 1 if any repos are not found in the database.
    """
    all_urls = _collect_urls(urls, url_file)

    if not all_urls:
        raise click.UsageError(
            "Provide at least one URL as an argument or via --file / -f."
        )

    # ── Validation ───────────────────────────────────────────────────────────
    # Partition into valid/invalid; always show invalids but keep going.
    invalid_urls = [u for u in all_urls if not is_valid_github_url(u)]
    valid_urls   = [u for u in all_urls if     is_valid_github_url(u)]

    if invalid_urls:
        click.echo(
            click.style(f"\n=== INVALID ({len(invalid_urls)}) ===", fg="yellow", bold=True),
            err=True,
        )
        for u in invalid_urls:
            click.echo(f"  {u}", err=True)
        click.echo("", err=True)

    if not valid_urls:
        raise click.ClickException("No valid URLs remain after validation; nothing to check.")

    # ── Database lookup ───────────────────────────────────────────────────────
    try:
        results = _check_repos_in_db(valid_urls)
    except Exception as exc:
        raise click.ClickException(f"Database error: {exc}") from exc

    found   = [(url, repo_id) for url, ok, repo_id in results if ok]
    missing = [url            for url, ok, _       in results if not ok]

    # ── Output ────────────────────────────────────────────────────────────────
    if output_path:
        _write_report(output_path, found, missing, invalid_urls)
        click.echo(f"Report written to {output_path}")
    else:
        if found:
            click.echo(click.style(f"\n=== FOUND ({len(found)}) ===", fg="green", bold=True))
            for url, repo_id in found:
                click.echo(f"  {url}  (repo_id={repo_id})")

        if missing:
            click.echo(click.style(f"\n=== MISSING ({len(missing)}) ===", fg="red", bold=True))
            for url in missing:
                click.echo(f"  {url}")

        click.echo(
            f"\nSummary: {len(found)} found, {len(missing)} missing"
            f" out of {len(results)} checked"
            + (f", {len(invalid_urls)} invalid" if invalid_urls else "")
            + "."
        )

    if missing:
        sys.exit(1)
