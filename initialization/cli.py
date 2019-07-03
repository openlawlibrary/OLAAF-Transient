import click
import initialization.authentication as authentication

@click.group()
def cli():
  pass


@cli.command()
@click.option('--repo-path', default='E:\\OLL2\library\\backup\\cityofsanmateo\\law-html', help='path to the html repository')
@click.option('--initial-commit', default='c2240d7a16d136659fe76d1db08ad9fd6ebbe35d', help='First commit representing state of the repository which should be entered into the database')
def initialize_hashes(repo_path, initial_commit):
  authentication.initialize_hashes(repo_path, initial_commit)

cli()
