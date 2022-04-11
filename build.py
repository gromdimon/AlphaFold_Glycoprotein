
# Import libraries
import argparse, joblib, os, sys
from azureml.core import Dataset, Run
import pandas as pd
import numpy as np

from colabfold.batch import get_queries
from colabfold.batch import run as foldrun
from colabfold.download import default_data_dir
from colabfold.utils import setup_logging
from pathlib import Path
from Bio import SeqIO

os.makedirs('outputs', exist_ok=True)

# Set the input parameters
parser = argparse.ArgumentParser()
parser.add_argument("--sequence_id", type=str, dest='sequence_id', help='Input Sequence ID')
parser.add_argument("--msa_mode", type=str, dest='msa_mode', help='msa mode')
parser.add_argument("--num_models", type=int, dest='num_models', help='number of structures to predict')
parser.add_argument("--num_recycles", type=int, dest='num_recycles', help='number of recycles')
parser.add_argument("--stop_at_score", type=int, dest='stop_at_score', help='early stop after reaching this p1DDT score.')

args = parser.parse_args()

# Get the experiment run context
run = Run.get_context()
ws = run.experiment.workspace

# Settings
# msa_mode = "MMseqs2 (UniRef+Environmental)" #["MMseqs2 (UniRef+Environmental)", "MMseqs2 (UniRef only)","single_sequence","custom"]
# num_models = 1
# num_recycles = 3
# stop_at_score = 90

sequence_id = args.sequence_id
msa_mode = args.msa_mode
num_models = args.num_models
num_recycles = args.num_recycles
stop_at_score = args.stop_at_score

use_custom_msa, use_amber, use_templates, do_not_overwrite_results, zip_results = False, False, False, False, False

# Log run options
run.log('sequence_id', str(sequence_id))
run.log('msa_mode', str(msa_mode))
run.log('num_models', str(num_models))
run.log('num_recycles', str(num_recycles))
run.log('stop_at_score', str(stop_at_score))

# Load sequences
print("Loading sequences...")
for record in SeqIO.parse("sequences.fasta", "fasta"):
    if sequence_id == record.description:
        # Write out the specific sequence fasta file for this node
        SeqIO.write(record, open("run_sequence.fasta", "w"), "fasta")

# Output and Input directories
result_dir = 'outputs/predicted_structures/'
input_dir = 'run_sequence.fasta'

# Set up Logging
setup_logging(Path(result_dir).joinpath("log.txt"))
# Set up query tasks (1 per input sequence)
queries, is_complex = get_queries(input_dir)

# Run Fold Prediction
foldrun(
    queries=queries,
    result_dir=result_dir,
    use_templates=use_templates,
    use_amber=use_amber,
    msa_mode=msa_mode,
    model_type="auto",
    num_models=num_models,
    num_recycles=num_recycles,
    model_order=[1],
    is_complex=is_complex,
    data_dir=default_data_dir,
    keep_existing_results=do_not_overwrite_results,
    rank_by="auto",
    pair_mode="unpaired+paired",
    stop_at_score=stop_at_score,
    zip_results=zip_results,
)

run.log('complete', np.int(1))

run.complete()
