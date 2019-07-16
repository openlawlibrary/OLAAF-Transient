import click
import initialization.hashes_init as hashes_init

@click.group()
def cli():
  pass


@cli.command()
@click.option('--repo-path', default='E:\\OLL2\\library\\transient_auth_test\\law-html', help='path to the html repository')
def initialize_hashes(repo_path):
  hashes_init.initialize_hashes(repo_path)

cli()
