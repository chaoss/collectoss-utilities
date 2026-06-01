# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s
from collectoss.application.db.session import DatabaseSession

from collectoss.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
)
from collectoss.application.db.models.augur_data import Repo
from collectoss.tasks.github.util.util import get_owner_repo

from ..repair import RepairToolMetadata

from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)


# This file contains a click command for fixing https://github.com/chaoss/CollectOSS/issues/310
@click.command(name="310")
@click.option("--dry-run", is_flag=True, default=False, help="Skip the final updating of values to demonstrate what work would be done without doing it")
@test_connection
@test_db_connection
@with_database
@click.pass_context
def command(ctx, dry_run):
    """Fixes issue #310:
    This was a bug where, due to an oversight in the repo move task, moved repos didnt have their repo_name updated correctly
    This retroactively updates those names to be accurate.
    """

    tool_source = RepairToolMetadata().name + " for issue #310"
    tool_version = RepairToolMetadata().version
    
    click.echo("Checking for mismatching repo_name values in the repo table (#310)...")

    with DatabaseSession(logger, ctx.obj.engine) as session:

        click.echo("\tcounting total affected rows...", nl=False)

        all_repos = session.execute(s.select(Repo)).scalars().all()

        click.echo(f"found {len(all_repos)} repos.")


        affected_repos = []

        unaffected_repos = []


        for r in all_repos:
            # cases: 1. name is changed, 2. name is shortened
            if not r.repo_name:
                click.echo(f"found repo with no name {r.repo_git} {r.repo_id}. Likely disabled, skipping.")
                unaffected_repos.append(r)
                continue
            if r.repo_name not in r.repo_git or not r.repo_git.endswith(r.repo_name):
                affected_repos.append(r)
            else:
                unaffected_repos.append(r)


        click.echo(f"found {len(affected_repos)} affected repos.")

        click.echo(f"found {len(unaffected_repos)} unaffected repos.")

        for a in affected_repos:
            current_owner, current_name = get_owner_repo(a.repo_git)
            action = "needs rename" if dry_run else "being renamed"
            click.echo(f"repo named {a.repo_name} (id: {a.repo_id}) {action} to {current_name}")
            if not dry_run:
                a.repo_name = current_name


        if dry_run:
            click.echo(f"No changes made because script was run in dry-run mode.")
        else:
            session.commit()
            click.echo(f"Done.")