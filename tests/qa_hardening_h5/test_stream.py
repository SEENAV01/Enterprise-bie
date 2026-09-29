from h5_helpers import *
from bie.qa.media_runtime_v2.stream import *
class Streaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.fm=tool('ffmpeg');cls.fp=tool('ffprobe')
        cls.art={name:encode(cls.root,name,mode=mode) for name,mode in [('healthy','normal'),('black','black'),('jump','jump'),('freeze','freeze'),('flash','flash')]}
        cls.policy=StreamPolicy(64,48,'12',12,chunk_frames=4,sample_frames=(0,4,11))
        cls.results={k:inspect(cls.root,v,bind(cls.policy),cls.policy,ffmpeg=cls.fm,ffprobe=cls.fp) for k,v in cls.art.items()}
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_real_decode_all_frames(self):
        r=self.results['healthy'];self.assertTrue(r['technical_checks_clear']);self.assertEqual(r['details']['frames'],12);self.assertTrue(validate_coverage(r['details'],self.policy))
    def test_cross_chunk_black_frame(self):self.assertIn('H5_BLANK_FRAME',codes(self.results['black']));self.assertEqual(self.results['black']['details']['first_defect_frames']['H5_BLANK_FRAME'],4)
    def test_cross_chunk_jump(self):self.assertIn('H5_UNEXPECTED_FRAME_JUMP',codes(self.results['jump']))
    def test_allowlisted_cut(self):
        p=replace(self.policy,allowed_cut_frames=(4,));r=inspect(self.root,self.art['jump'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp);self.assertNotIn('H5_UNEXPECTED_FRAME_JUMP',codes(r))
    def test_approved_blank_window(self):
        p=replace(self.policy,blank_windows=((4,5),));r=inspect(self.root,self.art['black'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp);self.assertNotIn('H5_BLANK_FRAME',codes(r))
    def test_required_motion_freeze(self):
        p=replace(self.policy,motion_windows=((0,12),),max_freeze_frames=3);r=inspect(self.root,self.art['freeze'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp);self.assertIn('H5_FROZEN_REQUIRED_MOTION',codes(r))
    def test_flash_screening(self):self.assertIn('H5_FLASH_SCREENING_LIMIT',codes(self.results['flash']))
    def test_absent_audio(self):
        p=replace(self.policy,require_audio=True);r=inspect(self.root,self.art['healthy'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp);self.assertIn('H5_REQUIRED_AUDIO_MISSING',codes(r))
    def test_wrong_dimensions(self):
        p=replace(self.policy,width=66)
        with self.assertRaisesRegex(ContractError,'H5_VIDEO_DIMENSIONS'):inspect(self.root,self.art['healthy'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp)
    def test_wrong_fps(self):
        p=replace(self.policy,fps='24')
        with self.assertRaisesRegex(ContractError,'H5_VIDEO_FRAME_RATE'):inspect(self.root,self.art['healthy'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp)
    def test_missing_frames(self):
        p=replace(self.policy,frames=13)
        with self.assertRaisesRegex(ContractError,'H5_MISSING_FRAMES'):inspect(self.root,self.art['healthy'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp)
    def test_extra_frames(self):
        p=replace(self.policy,frames=11,sample_frames=(0,4,10))
        with self.assertRaisesRegex(ContractError,'H5_EXCESS_FRAMES'):inspect(self.root,self.art['healthy'],bind(p),p,ffmpeg=self.fm,ffprobe=self.fp)
    def test_sample_png_bytes_from_decoder(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'frames';r=inspect(self.root,self.art['healthy'],bind(self.policy),self.policy,ffmpeg=self.fm,ffprobe=self.fp,samples_dir=d)
            for s in r['details']['samples']:self.assertEqual(hashlib.sha256((d/s['path']).read_bytes()).hexdigest(),s['png_sha256'])
    def test_sample_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileExistsError):inspect(self.root,self.art['healthy'],bind(self.policy),self.policy,ffmpeg=self.fm,ffprobe=self.fp,samples_dir=td)
    def test_replayed_foreign_policy(self):
        with self.assertRaisesRegex(ContractError,'H5_POLICY_BINDING'):inspect(self.root,self.art['healthy'],replace(bind(self.policy),policy_digest='0'*64),self.policy,ffmpeg=self.fm,ffprobe=self.fp)
    def test_omitted_chunk(self):
        d=copy.deepcopy(self.results['healthy']['details']);d['chunks'].pop(1)
        with self.assertRaisesRegex(ContractError,'H5_FRAME_CHUNK_GAP'):validate_coverage(d,self.policy)
    def test_missing_sample(self):
        d=copy.deepcopy(self.results['healthy']['details']);d['samples'].pop()
        with self.assertRaisesRegex(ContractError,'H5_SAMPLE_COVERAGE'):validate_coverage(d,self.policy)
    def test_wrong_decoded_bytes(self):
        d=copy.deepcopy(self.results['healthy']['details']);d['decoded_bytes']-=3
        with self.assertRaisesRegex(ContractError,'H5_DECODED_BYTE_COUNT'):validate_coverage(d,self.policy)
    def test_memory_guard(self):
        with self.assertRaisesRegex(ContractError,'H5_FRAME_MEMORY_BUDGET'):StreamPolicy(3840,2160,'30',1,max_working_pixel_bytes=1024)
    def test_no_technical_video_success_is_acceptance(self):
        r=self.results['healthy'];self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.assertFalse(r['production_authorized'])

class SpatialReduction(unittest.TestCase):
    def test_strided_reduction_matches_full_reference(self):
        rng=np.random.default_rng(8)
        for n in (1,2,15,127,4096,10000):
            with self.subTest(pixels=n):
                x=rng.integers(0,256,size=n*3,dtype=np.uint8);self.assertEqual(spatial_range(x),int(np.ptp(x.reshape(-1,3),axis=0).max()))
    def test_solid_colored_frame_is_uniform(self):
        x=np.tile(np.array([10,80,250],dtype=np.uint8),1000);self.assertEqual(spatial_range(x),0)
