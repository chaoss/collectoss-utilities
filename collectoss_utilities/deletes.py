import click


def generate_delete_script(repo_ids, output_sql_file):
    output = []

    for repo_id in repo_ids:
        output.append("BEGIN;")
        output.append(f"delete from augur_data.issue_message_ref WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_review_message_ref WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_message_ref WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_info WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.issue_assignees WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.releases WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_reviews WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_files WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_commits WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_requests WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_badging WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.issues WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_deps_libyear WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_deps_scorecard WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_dependencies WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.commits WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo_labor WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.message WHERE repo_id = {repo_id};")
        output.append("--")
        output.append(f"delete from augur_operations.user_repos where repo_id = {repo_id};")
        output.append(f"delete from augur_operations.collection_status where repo_id = {repo_id};")
        output.append(f"delete from augur_data.commit_messages where repo_id = {repo_id};")
        output.append(f"delete from augur_data.issue_events WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.issue_labels WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_labels WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_events WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_meta WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_reviewers WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.pull_request_assignees WHERE repo_id = {repo_id};")
        output.append(f"delete from augur_data.repo where repo_id = {repo_id};")
        output.append("COMMIT;\n")

    if output_sql_file:
        with open(output_sql_file, "w", encoding="utf-8") as f:
            f.writelines(output)
    else:
        for i in output:
            print(i)


@click.command(name="delete-repos")
@click.argument('repo_ids',type=int, required=True, nargs=-1) #, help="Repo ID(s) to generate delete script for"
@click.option(
    "-o",
    "--output",
    "output_sql_file",
    type=click.Path(dir_okay=False, writable=True),
    required=False,
    help="Path to write the generated SQL file.",
)
def command(repo_ids, output_sql_file):
    """Generate SQL to delete one or more repos from a CollectOSS database."""
    generate_delete_script(repo_ids, output_sql_file)
