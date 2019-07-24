import click

from gandalf.application import validate_xml
from gandalf.application import Compare
from gandalf.application import ParseMusic21
from gandalf.extra import output_filter


@click.group()
@click.option("-p/--pretty-print", default=False, help="Print the output with and automatic indent.")
@click.option("-n/--notes", default=False, help="Show note objects")
@click.option("-r/--rests", default=False, help="Show rest objects")
@click.option("-t/--time-signatures", default=False, help="Show the time signatures")
@click.option("-k/--key-signatures", default=False, help="Show the key signatures")
@click.option("-c/--clefs", default=False, help="Show the clefs")
@click.pass_context
def cli(ctx, p, n, r, t, k, c):
  """
  This tool helps parse MusicXML files and can list how many discrepancies there are, and what they are.
  Feed it any musicXML file and it will list all of its contents, or compare a musicXML file with a
  "ground truth" musicXML file that you know to be correct. It will list how many mistakes there are, and
  what they are aswell.
  """


@cli.command("compare", short_help="Compare two or more MusicXML files. You may also select the type of algorithm you want to use by specifying --sort=anw")  # noqa
@click.option("--sort", default="basic", help="Note alignment algorithm to use when aligning Gandalf objects.")
@click.argument("true_data")
@click.argument("test_data", nargs=-1)
@click.pass_context
def compare(ctx, sort, true_data, test_data):
  """
  Compares two MusicXML files.
    --sort=basic    Uses a dumb alignment that does not look forward or backward in time.
    --sort=anw      Uses a simplistic version of the Affine-Needleman-Wunsch based on
                      a single element from the Gandalf Objects.

    <ground truth file> <file or files to parse through>
  """
  for f in test_data:
    output_filter(
      ctx.parent.params,
      Compare,
      true_filepath=true_data,
      test_filepath=f,
      sorting_algorithm=sort,
    )


@cli.command("read", short_help="Show the parsed Symbolic file as a list of elements")
@click.argument("file_path", nargs=-1)
@click.pass_context
def read(ctx, file_path):
  """
  """
  for f in file_path:
    output_filter(ctx.parent.params, ParseMusic21.from_filepath, f)


@cli.command("validate", short_help="Check if MusicXML file is valid.")
@click.argument("file_path", nargs=-1)
def validate(file_path):
  """
  """
  for f in file_path:
    print(f"{f}: {validate_xml(f)}")
