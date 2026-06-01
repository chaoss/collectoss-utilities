# SPDX-License-Identifier: MIT
import logging
import click
import sqlalchemy as s
from collectoss.application.db.session import DatabaseSession

from collectoss.application.cli import (
    test_connection,
    test_db_connection,
    with_database,
    DatabaseContext,
)
from collectoss.application.db.models.augur_data import Repo
from collectoss.tasks.github.util.util import get_owner_repo


from pygit2 import Repository, GitError
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



    #     click.echo(f"\tFetching the affected repos...")

    #     # any queries that attempt to get one row per commit are incredibly slow
    #     query = s.select(func.distinct(Commit.repo_id)).where(Commit.cmt_author_name == '')
    #     repos = session.execute(query).scalars().all()
    
    #     # click.echo("\tProcessing empty commit authors")

    #     # append_log_file(affected_repos_file, repos)


    #     for repo_id in repos:

    #         repo = get_repo_by_repo_id(repo_id)
         
    #         #Get the huge list of commits to process.
    #         absolute_path = get_absolute_repo_path(repo_base_directory, repo.repo_id, repo.repo_path, repo.repo_name)
    #         repo_loc = (f"{absolute_path}/.git")
    #         try:
    #             lg2_repo = Repository(repo_loc)
    #         except GitError as e:
    #             click.echo(f"Error opening repo: ")
    #             click.echo(e)
    #             continue

    #         click.echo(f"\tFetching affected commits in repo id {repo_id}, path {absolute_path}...", nl=False)
    #         query = s.select(func.distinct(Commit.cmt_commit_hash)).where(Commit.cmt_author_name == '', Commit.repo_id == repo_id)
    #         unique_commit_hashes = session.execute(query).scalars().all()
    #         # append_log_file(affected_commits_file, unique_commit_hashes)
    #         click.echo(len(unique_commit_hashes))

    #         for commithash in unique_commit_hashes:
    #             commit = lg2_repo[commithash]
                
    #             # any queries that attempt to get one row per commit are incredibly slow
    #             query = s.select(Commit).where(Commit.cmt_author_name == '', Commit.repo_id == repo.repo_id, Commit.cmt_commit_hash == commithash)
    #             commit_changes = session.execute(query).scalars().all()

    #             # fetch all records with this commit hash
    #             click.echo(f"\t{len(commit_changes)} commit change records match hash {commithash}")
                
    #             # append_log_file(all_affected_rows_file, commit_changes)


    #             conditions = [all((
    #                 s.cmt_author_email == commit.author.email,
    #                 s.cmt_committer_name == commit.committer.name,
    #                 s.cmt_committer_email == commit.committer.email,
    #                 # s.cmt_committer_email == commit.committer.email,
    #                 s.cmt_commit_hash == commithash
    #             )) for s in commit_changes]
    #             # click.echo(f"sanity check: {all(conditions)}")
    #             if all(conditions) == True:
    #                 if not dry_run:
    #                     query = ( s.update(Commit)
    #                         .where(Commit.cmt_author_name == '', Commit.repo_id == repo.repo_id, Commit.cmt_commit_hash == commithash)
    #                         .values({
    #                             'cmt_author_name': commit.author.name,
    #                             'tool_version': tool_version,
    #                             'tool_source': tool_source,
    #                         })
    #                     )
    #                     session.execute(query)
    #             else:
    #                 pass
    #                 # # click.echo(repr(sample))
    #                 # click.echo(repo.repo_git)
    #                 # click.echo(commithash)
    #                 # click.echo(f"{sample.cmt_author_email} ({sample.cmt_author_raw_email})")
    #                 # click.echo(commit.author.email)
    #                 # click.echo(sample.cmt_committer_name)
    #                 # click.echo(commit.committer.name)
    #                 # click.echo(f"{sample.cmt_committer_email} ({sample.cmt_committer_raw_email})")
    #                 # click.echo(commit.committer.email)
    #                 # click.echo(commit.message)
    #                 # click.echo(commit.parent_ids)
    #                 # click.prompt("enter any value and press enter to continue")
                    
    #         session.commit()
                        
