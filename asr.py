from kaldi.asr import GmmLatticeFasterRecognizer, NnetLatticeFasterOnlineRecognizer
from kaldi.decoder import LatticeFasterDecoderOptions
from kaldi.feat.mfcc import Mfcc, MfccOptions
from kaldi.feat.functions import compute_deltas, DeltaFeaturesOptions
from kaldi.feat.window import FrameExtractionOptions
from kaldi.transform.cmvn import Cmvn
from kaldi.util.options import ParseOptions
from kaldi.util.table import SequentialWaveReader, SequentialMatrixReader
from kaldi.nnet3 import NnetSimpleLoopedComputationOptions
from kaldi.online2 import (
    OnlineEndpointConfig,
    OnlineIvectorExtractorAdaptationState,
    OnlineNnetFeaturePipelineConfig,
    OnlineNnetFeaturePipelineInfo,
    OnlineNnetFeaturePipeline,
    OnlineSilenceWeighting,
)
from kaldi.matrix import SubVector
from itertools import zip_longest
import numpy as np
import webrtcvad

class ASR_from_files() :
    def __init__(self) -> None:
        # Construct recognizer
        decoder_opts = LatticeFasterDecoderOptions()
        decoder_opts.beam = 13.0
        decoder_opts.max_active = 7000
        self.model_path="model/tugas_akhir_win/exp/hmm-gmm/tri-lda-mllt"
        self.asr_from_files = GmmLatticeFasterRecognizer.from_files(
            "{}/final.mdl".format(self.model_path),
            "{}/graph/HCLG.fst".format(self.model_path),
            "{}/graph/words.txt".format(self.model_path),
            decoder_opts=decoder_opts
        )

        frame_opts = FrameExtractionOptions()
        frame_opts.samp_freq = 16000
        frame_opts.allow_downsample = True
        mfcc_opts = MfccOptions()
        mfcc_opts.use_energy = False
        mfcc_opts.frame_opts = frame_opts
        self.feat_pipeline = self.make_feat_pipeline(Mfcc(mfcc_opts))

        

    def make_feat_pipeline(self, base, opts=DeltaFeaturesOptions()) :
        def feat_pipeline(wav_file) :
            feats = base.compute_features(wav_file.data()[0], wav_file.samp_freq, 1.0)
            cmvn = Cmvn(base.dim())
            cmvn.accumulate(feats)
            cmvn.apply(feats)
            return compute_deltas(opts, feats)
        return feat_pipeline

    def decode(self, wav_file, scp_file="") :
        result = ""
        feats_rspecifier = (
            "ark:kaldi/src/featbin/compute-mfcc-feats --config=conf/mfcc.conf scp:" + scp_file + " ark:-"
            " | kaldi/src/featbin/apply-cmvn-sliding --cmn-window=10000 --center=true ark:- ark:-"
            " | kaldi/src/featbin/splice-feats --config=conf/splice.conf ark:- ark:-"
            " | kaldi/src/featbin/transform-feats {}/final.mat ark:- ark:- |".format(self.model_path)
        )
        if "lda" in self.model_path or "sat" in self.model_path :
            for key, feats in SequentialMatrixReader(feats_rspecifier) :
                out = self.asr_from_files.decode(feats)
                result = key + " " + out["text"]
                # print(key, out['text'], flush=True)
        else :
            rspec = "scp:"
            for key, wav in SequentialWaveReader(rspec + wav_file) :
                feats = self.feat_pipeline(wav)
                out = self.asr_from_files.decode(feats)
                result = key + " " + out["text"]
        return result

class ASR_live() :
    def __init__(self, VAD_buffer=5) -> None:
        # Kaldi init options
        online_conf = "conf/online.conf"

        feat_opts = OnlineNnetFeaturePipelineConfig()
        endpoint_opts = OnlineEndpointConfig()
        po = ParseOptions("")
        feat_opts.register(po)
        endpoint_opts.register(po)
        po.read_config_file(online_conf)
        self.feat_info = OnlineNnetFeaturePipelineInfo.from_config(feat_opts)

        # Construct recognizer
        decoder_opts = LatticeFasterDecoderOptions()
        decoder_opts.beam = 13
        decoder_opts.max_active = 7000
        decodable_opts = NnetSimpleLoopedComputationOptions()
        decodable_opts.acoustic_scale = 1.0
        decodable_opts.frame_subsampling_factor = 3
        decodable_opts.frames_per_chunk = 150
        self.asr_live = NnetLatticeFasterOnlineRecognizer.from_files(
            "model/tugas_akhir_2/exp/nnet3/mono_ali/final.mdl",
            "model/tugas_akhir_2/exp/nnet2/mono_ali/graph/HCLG.fst",
            "model/tugas_akhir_2/exp/nnet2/mono_ali/graph/words.txt",
            decoder_opts=decoder_opts,
            decodable_opts=decodable_opts,
            endpoint_opts=endpoint_opts
        )

        self.vad_frame_duration = 10
        self.vad = webrtcvad.Vad(2)
        self.current_activity_states = [False] * VAD_buffer
    
    def listen(self, stream, chunk_size) :
        return stream.read(chunk_size)

    def VAD(self, stream_data, sample_rate, frame_duration=10) :
        mini_chunk_size = (
            int(sample_rate * frame_duration / 1000) * 2
        )

        def chunker(chunk, n=mini_chunk_size, fillvalue=0) :
            args = [iter(chunk)] * n
            return zip_longest(*args, fillvalue=fillvalue)
        
        activity = []

        for mini_chunk in chunker(stream_data) :
            mini_chunk_bytes = bytes(mini_chunk)
            activity.append(self.vad.is_speech(mini_chunk_bytes, sample_rate))

        self.update_activity(any(activity))
        return any(activity)
    
    def update_activity(self, activity) :
        assert type(activity) == bool
        self.current_activity_states.append(activity)
        self.current_activity_states = self.current_activity_states[1:]

    def init_decoder(self) :
        self.feature_pipeline = OnlineNnetFeaturePipeline(self.feat_info)
        self.asr_live.set_input_pipeline(self.feature_pipeline)
        self.asr_live.init_decoding()
    
    def decode_chunk(self, chunk, sample_rate, last_chunk=False) :
        chunk = SubVector(chunk)
        if chunk.is_zero() :
            print("Data is zero")

        self.feature_pipeline.accept_waveform(sample_rate, chunk)

        if last_chunk :
            self.feature_pipeline.input_finished()
        
        self.asr_live.advance_decoding()

        if not last_chunk :
            out = self.asr_live.get_partial_output()
            return out['text']

        return ""

    def destroy_decoder(self) :
        self.asr_live.finalize_decoding()
        out = self.asr_live.get_output()
        return out['text']
    
    def run(self, stream, chunk_size, sample_rate) :
        chunk = self.listen(stream, chunk_size)
        self.init_decoder()
        chunk_array = np.asarray(np.fromstring(chunk, dtype=np.int16))
        activity = self.VAD(chunk, sample_rate)
        self.update_activity(activity=activity)

        while self.current_activity_states.count(True) > 2 :
            chunk = self.listen(stream, chunk_size)
            chunk_array = np.asarray(np.fromstring(chunk, dtype=np.int16))
            activity = self.VAD(chunk, sample_rate)
            if self.current_activity_states[0] and not any(self.current_activity_states[2:]) :
                self.update_activity(activity=activity)
                self.decode_chunk(chunk_array, sample_rate, last_chunk=True)
                final_output = self.destroy_decoder()
                print(final_output)
                # out = 
                break
            partial_output = self.decode_chunk(chunk_array, sample_rate, last_chunk=False)
            print(partial_output)
            print(self.current_activity_states)
