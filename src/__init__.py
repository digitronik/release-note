from shutil import get_terminal_size

import click
import tabulate

from .github import GitHub

COLUMNS = get_terminal_size().columns
HEADERS = ["MR", "Title"]


def clean_title(title):
    """Remove status instructions from title"""
    replacements = ["RFR", "WIP", "[", "]", ":"]
    for replacement in replacements:
        title = title.replace(replacement, "")
    return title.strip().capitalize()


@click.command()
@click.option(
    "-p",
    "--platform",
    default="github",
    type=click.Choice(["github", "gitlab"]),
    help="Repository hosting platform.",
)
@click.option("-u", "--username", default=None, help="Username/org name.")
@click.option("-r", "--repository", default=None, help="Repository name.")
@click.option(
    "--tablefmt",
    default="github",
    type=click.Choice(tabulate.tabulate_formats),
    help="Table Format",
)
@click.option("-a", "--author", is_flag=True, help="Include author in report")
@click.option("-l", "--labels", is_flag=True, help="Include labels in report")
@click.option("-c", "--complete", is_flag=True, help="Complete report")
def main(platform, username, repository, tablefmt, author, labels, complete):
    """Release Note"""
    if platform == "github":
        if not username:
            username = click.prompt("Username/org name")
        if not repository:
            repository = click.prompt("Repository name")

        gh = GitHub(org=username, project=repository)
    else:
        click.echo("Not supported for now.")

    last_tag = gh.last_release()
    prs = gh.merged_prs(last_tag.create_at)
    # ["number", "link", "title", "desc", "user_login", "user_link"]

    if complete:
        HEADERS.extend(["Author", "Labels"])
        tbl = [
            [
                f"[{pr.number}]({pr.link})",
                clean_title(pr.title),
                f"[{pr.user_login}]({pr.user_link})",
                ", ".join(pr.labels),
            ]
            for pr in prs
        ]
    elif author:
        HEADERS.append("Author")
        tbl = [
            [
                f"[{pr.number}]({pr.link})",
                clean_title(pr.title),
                f"[{pr.user_login}]({pr.user_link})",
            ]
            for pr in prs
        ]
    elif labels:
        HEADERS.append("Labels")
        tbl = [
            [f"[{pr.number}]({pr.link})", clean_title(pr.title), ", ".join(pr.label)] for pr in prs
        ]
    else:
        tbl = [[f"[{pr.number}]({pr.link})", clean_title(pr.title)] for pr in prs]

    click.echo(
        f"\n\n<!-- {'-' * int((COLUMNS - 25)/2)} Copy Changelog {'-' * int((COLUMNS - 25)/2)} -->\n"
    )
    click.echo(tabulate.tabulate(tbl, headers=HEADERS, tablefmt=tablefmt))
    click.echo(f"<!-- {'-' * (COLUMNS - 9)} -->\n")
