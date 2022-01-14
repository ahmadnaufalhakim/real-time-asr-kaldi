from __future__ import print_function

from kaldi.asr import GmmLatticeFasterRecognizer, NnetLatticeFasterOnlineRecognizer
from kaldi.decoder import LatticeFasterDecoderOptions, FasterDecoderOptions
from kaldi.feat.mfcc import Mfcc, MfccOptions
from kaldi.feat.functions import splice_frames, compute_deltas, DeltaFeaturesOptions
from kaldi.feat.window import FrameExtractionOptions
from kaldi.transform.cmvn import Cmvn
from kaldi.util.table import SequentialMatrixReader, SequentialWaveReader
from kaldi.util.options import ParseOptions
from kaldi.nnet3 import NnetSimpleLoopedComputationOptions

# Construct recognizer
## asr
decoder_opts = LatticeFasterDecoderOptions()
decoder_opts.beam = 11.0
decoder_opts.max_active = 7000

model_path = "tri-2delta"
asr = GmmLatticeFasterRecognizer.from_files(
    # # tugas_akhir_2
    # "model/tugas_akhir_2/exp/hmm-gmm/{}/final.mdl".format(model_path),
    # "model/tugas_akhir_2/exp/hmm-gmm/{}/graph/HCLG.fst".format(model_path),
    # "model/tugas_akhir_2/exp/hmm-gmm/{}/graph/words.txt".format(model_path),

    # tugas_akhir_win
    "model/tugas_akhir_win/exp/hmm-gmm/{}/final.mdl".format(model_path),
    "model/tugas_akhir_win/exp/hmm-gmm/{}/graph/HCLG.fst".format(model_path),
    "model/tugas_akhir_win/exp/hmm-gmm/{}/graph/words.txt".format(model_path),
    decoder_opts=decoder_opts
)
print(asr)
print("-" * 80, flush=True)

# Feature pipeline
## Define feature pipeline as a Kaldi rspecifier
feats_rspecifier = (
    "ark:kaldi/src/featbin/compute-mfcc-feats --config=conf/mfcc.conf scp:data/dec_wav.scp ark:-"
    " | kaldi/src/featbin/apply-cmvn-sliding --cmn-window=10000 --center=true ark:- ark:-"
    " | kaldi/src/featbin/add-deltas ark:- ark:- |"
    )

## Define feature pipeline in code
def make_feat_pipeline(base, opts=DeltaFeaturesOptions()):
    def feat_pipeline(wav):
        feats = base.compute_features(wav.data()[0], wav.samp_freq, 1.0)
        cmvn = Cmvn(base.dim())
        cmvn.accumulate(feats)
        cmvn.apply(feats)
        return compute_deltas(opts, feats)
    return feat_pipeline

frame_opts = FrameExtractionOptions()
frame_opts.samp_freq = 16000
frame_opts.allow_downsample = True
mfcc_opts = MfccOptions()
mfcc_opts.use_energy = False
mfcc_opts.frame_opts = frame_opts
feat_pipeline = make_feat_pipeline(Mfcc(mfcc_opts))

# Decode
# # Decode using code feats pipeline
# for key, wav in SequentialWaveReader("scp:data/dec_wav.scp"):
#     feats = feat_pipeline(wav)
#     out = asr.decode(feats)
#     print(key, out['text'], flush=True)

## Decode using feats_rspecifier
for key, feats in SequentialMatrixReader(feats_rspecifier) :
    out = asr.decode(feats)
    print(key, out['text'], flush=True)

print("-" * 80, flush=True)
