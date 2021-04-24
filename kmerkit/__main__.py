#!/usr/bin/env python

"""
TODO:
We could develop command line tools that combine multiple class calls together.

kcount --name hybridus \
       --workdir /tmp \
       --fastqs ~/Documents/ipyrad/isolation/reftest_fastqs/[1-2]*_0_R*_.fastq.gz \
       --trim \
       --canonical \
       --kmersize 31 \
	   --mindepth 1 \


ktree --name hybridus \
	  --workdir /tmp \
      --tree hybridus-tree.nwk \
      --model ... \
      --threshold ... \
      --target-options ... \
"""

from enum import Enum
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Union
import typer
from kmerkit import __version__
from kmerkit.utils import set_loglevel, KmerkitError
from kmerkit.utils import get_fastq_dict_from_path, get_traits_dict_from_csv
from kmerkit.kinit import init_project
from kmerkit.kcount import Kcount
from kmerkit.kfilter import Kfilter
from kmerkit.kextract import Kextract

# add the -h option for showing help
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
 

class LogLevel(str, Enum):
    "categorical options for loglevel to CLI"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# creates the top-level kmerkit app
app = typer.Typer(add_completion=True, context_settings=CONTEXT_SETTINGS)

@app.callback()
def callback():
    """
    Call kmerkit commands to access tools in the kmerkit toolkit, 
    and kmerkit COMMAND -h to see help options for each tool
    (e.g., kmerkit kcount -h)
    """
    typer.secho(
        f"kmerkit (v.{__version__}): the kmer operations toolkit",
        fg=typer.colors.MAGENTA, bold=True,
    )

@app.command()
def docs():
    "opens the kmerkit documentation in a browser"
    typer.echo("Opening kmerkits documentation in browser")
    typer.launch("https://kmerkit.readthedocs.io")


@app.command()
def info(
    json_file: str = typer.Option(..., "--json", "-j", help="kmerkit project JSON file"),
    flow: bool = typer.Option(False, help="show status as flow diagram"),
    stats: bool = typer.Option(False, help="show per-sample stats"),
    ):
    """
    Show status or flow diagram of project
    """
    # print the stats (json?) file location
    # typer.secho(
        # f"project path: {workdir}/{name}", fg=typer.colors.CYAN)

    # TODO: create a class for stats and progress all in JSON

    # shows a flowchart based on progress
    if flow:
        pass

    if stats:
        pass



@app.command(context_settings=CONTEXT_SETTINGS)
def init(
    name: str = typer.Option(
        "test",
        "-n", "--name",
        help="Prefix for output files.",
        ),
    workdir: str = typer.Option(
        tempfile.gettempdir(), 
        "-w", "--workdir",
        help="Dir name for output files.",
        ),

    force: bool = typer.Option(
        False,
        help="force overwrite of existing JSON file."
        ),
    # sample: Optional[List[str]] = typer.Option(None),
    delim: str = typer.Option("_R"),
    loglevel: LogLevel = LogLevel.INFO,
    data: List[Path] = typer.Argument(...,
        show_default=False,
        exists=True,
        dir_okay=True,
        file_okay=True,
        resolve_path=False,
        allow_dash=True,
        help=("File path(s) to input fastq/a data files")
        ),
    # trim_reads: bool = typer.Option(True),
    # subsample_reads: int = typer.Option(None),
    ):
    """
    Initialize a kmerkit project.

    Creates a JSON project file in <workdir>/<name>.json. Sample
    names are parsed from input filenames by splitting on the last
    occurrence of the optional 'delim' character (default is '_R').
    Paired reads are automatically detected from _R1 and _R2 in names.
    Examples:

    kmerkit init -n test -w /tmp ./data/fastqs/*.gz\n
    kmerkit init -n test -w /tmp ./data-1/A.fastq ./data-2/B.fastq
    """
    # parse the fastq_dict from string
    set_loglevel(loglevel)
    fastq_dict = get_fastq_dict_from_path(None, data, delim)

    try:
        init_project(name=name, workdir=workdir, fastq_dict=fastq_dict, force=force)
    except KmerkitError:
        typer.Abort()



@app.command(context_settings=CONTEXT_SETTINGS)
def count(
    json_file: Path = typer.Option(..., "-j", "--json"),
    kmer_size: int = typer.Option(17, min=2),
    min_depth: int = typer.Option(1, min=1),
    max_depth: int = typer.Option(int(1e9), min=1),
    max_count: int = typer.Option(255, min=1),
    canonical: bool = typer.Option(True),
    threads: int = typer.Option(2),
    force: bool = typer.Option(False, help="overwrite existing results."),
    loglevel: LogLevel = LogLevel.INFO,
    ):
    """
    Count kmers in fastq/a files using KMC. 

    kcount will write kmer database files for each sample to 
    <workdir>/<name>_kcount_.kmc_[suf,pre]. Example:

    kmerkit count -j test.json --kmer-size 35 --min-depth 5
    """
    # report the module
    typer.secho(
        "count: counting kmers from fastq/a files using KMC",
        fg=typer.colors.MAGENTA,
        bold=False,
    )

    # set the loglevel
    set_loglevel(loglevel)
    typer.secho(
        f"loglevel: {loglevel}, logfile: STDERR",
        fg=typer.colors.MAGENTA,
        bold=False,
    )

    # run the command
    counter = Kcount(
        str(json_file),
        kmer_size=kmer_size,
        min_depth=min_depth,
        max_depth=max_depth,
        max_count=max_count,
        canonical=canonical,
    )
    # print(counter.statsdf.T)
    try:
        counter.run(threads=threads, force=force)
    except KmerkitError as exc:
        typer.Abort(exc)



@app.command()
def filter(
    json_file: Path = typer.Option(..., '-j', '--json'),
    traits: Path = typer.Option(...),
    min_cov: float = typer.Option(0.5),
    min_map: Tuple[float,float] = typer.Option((0.0, 0.1)),
    max_map: Tuple[float,float] = typer.Option((0.1, 1.0)),
    loglevel: LogLevel = LogLevel.INFO,
    force: bool = typer.Option(False, help="overwrite existing results."),
    # min_map_canon
    ):
    """
    filter kmers based on distribution among samples/traits
    """
    # report the module
    typer.secho(
        "filter: filter kmers based on frequency in case/control groups",
        fg=typer.colors.MAGENTA,
        bold=False,
    )
    # set the loglevel
    set_loglevel(loglevel)
    typer.secho(
        f"loglevel: {loglevel}, logfile: STDERR",
        fg=typer.colors.MAGENTA,
        bold=False,
    )

    # fake data
    traits_dict = get_traits_dict_from_csv(traits)

    # load database with phenotypes data
    kgp = Kfilter(
        json_file=json_file,
        traits=traits_dict,
        min_cov=min_cov,
        min_map={0: min_map[0], 1: min_map[1]},
        max_map={0: max_map[0], 1: max_map[1]},        
        min_map_canon={0: 0.0, 1: 0.5},
    )
    kgp.run()


@app.command()
def extract(
    json_file: Path = typer.Option(..., '-j', '--json'),
    min_kmers_per_read: int = typer.Option(1),
    keep_paired: bool = typer.Option(True),
    loglevel: LogLevel = LogLevel.INFO,
    force: bool = typer.Option(False, help="overwrite existing results."),  
    samples: List[str] = typer.Argument(None),
    ):
    """
    Extract reads from fastq/a files that contain at least
    'min-kmers-per-read' kmers in them. If 'keep-paired' then reads
    are returns as paired-end. Samples can be entered as arguments
    in three possible ways: (1) enter sample names that are in the
    init database; (2) enter an integer for group0 or group1 from
    the kfilter database; (3) enter a file path to one or more
    fastq files.

    kmerkit extract -j test.json A B C D      # select from init\n
    kmerkit extract -j test.json 1            # select from filter group\n
    kmerkit extract -j test.json ./data/*.gz  # select new files\n
    """
    typer.secho(
        "extract: extract reads containing target kmers",
        fg=typer.colors.MAGENTA,
        bold=False,
    )
    set_loglevel(loglevel)
    kex = Kextract(
        json_file=json_file,
        samples=samples,
        min_kmers_per_read=min_kmers_per_read,
        keep_paired=keep_paired,
    )
    kex.run(force=force)
