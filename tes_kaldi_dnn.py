from __future__ import print_function

from kaldi.asr import NnetLatticeFasterRecognizer, LatticeLmRescorer
from kaldi.decoder import LatticeFasterDecoderOptions
from kaldi.fstext import SymbolTable, shortestpath, indices_to_symbols
from kaldi.fstext.utils import get_linear_symbol_sequence
from kaldi.nnet3 import NnetSimpleComputationOptions
from kaldi.util.table import SequentialMatrixReader

# Construct recognizer
decoder_opts = LatticeFasterDecoderOptions()
decoder_opts.beam = 13
decoder_opts.max_active = 7000
decodable_opts = NnetSimpleComputationOptions()
decodable_opts.acoustic_scale = 1.0
decodable_opts.frame_subsampling_factor = 3
decodable_opts.frames_per_chunk = 150
asr = NnetLatticeFasterRecognizer.from_files(
    "model/tugas_akhir_2/exp/nnet3/mono_ali",
    "model/tugas_akhir_2/exp/nnet2/mono_ali/graph/HCLG.fst",
    decoder_opts=decoder_opts,
    decodable_opts=decodable_opts
)

# Construct symbol table
symbols = SymbolTable.read_text("model/tugas_akhir_2/exp/nnet2/mono_ali/graph/words.txt")
phi_label = symbols.find_index("#0")

# Construct LM rescorer
rescorer = LatticeLmRescorer.from_files(
    "model/tugas_akhir_2/data/lang/G.fst",
    "model/tugas_akhir_2/data/lang/G.rescore.fst",
    phi_label
)

# Define feature pipelines as Kaldi rspecifiers
feats_rspec = "ark:kaldi/src/featbin/compute-mfcc-feats --config=mfcc.conf scp:data/dec_wav.scp ark:- |"
ivectors_rspec = (
    "ark:kaldi/src/featbin/compute-mfcc-feats --config=mfcc.conf scp:data/dec_wav.scp ark:-"
    " | "
)