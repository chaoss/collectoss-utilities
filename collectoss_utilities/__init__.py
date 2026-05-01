import click
from collectoss_utilities.repair import repair

@click.group()
def cli():
    """CollectOSS-utilities: utilities for one-off repairs and recovery for CollectOSS instances"""
    pass

cli.add_command(repair)