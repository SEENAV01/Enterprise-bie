"""H2-003: exact stream inventory and resource admission before full decoding."""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, strict_loads
from .process import capture, executable
from .custody import integer

FORMATS='matroska,webm,mov'

def input_args(path):
    # No playlists, concat, URL protocols, external references or auto-rotation.
    return ['-protocol_whitelist','file,pipe','-format_whitelist',FORMATS,'-i',str(path)]

def fraction(value):
    if type(value) not in (str,int,float) or isinstance(value,bool) or len(str(value))>80:
        raise BenchmarkError('INVALID_MEDIA_FRACTION')
    try:
        x=Fraction(str(value))
        if abs(x)>10**10:raise ValueError()
        return x
    except (ValueError,ZeroDivisionError,OverflowError) as e: raise BenchmarkError('INVALID_MEDIA_FRACTION') from e

def inspect(path,limits,deadline):
    argv=[executable('ffprobe'),'-v','error',*input_args(path),'-show_streams','-show_format','-of','json']
    raw,command=capture(argv,path.parent,deadline,limits.max_metadata_bytes)
    try: data=strict_loads(raw.decode('utf-8'))
    except UnicodeError as e: raise BenchmarkError('MEDIA_METADATA_ENCODING') from e
    if type(data) is not dict or type(data.get('streams')) is not list: raise BenchmarkError('MEDIA_METADATA_SCHEMA')
    streams=data['streams']
    if any(type(s) is not dict for s in streams):raise BenchmarkError('MEDIA_METADATA_SCHEMA')
    vs=[s for s in streams if s.get('codec_type')=='video'];aus=[s for s in streams if s.get('codec_type')=='audio']
    if len(vs)!=1: raise BenchmarkError('EXACTLY_ONE_VIDEO_REQUIRED')
    if len(aus)>1: raise BenchmarkError('AUDIO_SELECTION_AMBIGUOUS')
    if len(streams)!=len(vs)+len(aus):raise BenchmarkError('UNSUPPORTED_EMBEDDED_STREAM')
    v=vs[0];w=integer(v.get('width'),1,limits.max_width);h=integer(v.get('height'),1,limits.max_height)
    fps=fraction(v.get('avg_frame_rate'))
    if not 0<fps<=120:raise BenchmarkError('MEDIA_FPS_LIMIT')
    if v.get('codec_name') not in ('h264','hevc','vp8','vp9','av1','ffv1','mpeg4'):
        raise BenchmarkError('UNSUPPORTED_VIDEO_CODEC')
    # Current statistics are SDR RGB8, not a HDR perception metric.
    if v.get('pix_fmt') not in ('yuv420p','yuv422p','yuv444p','rgb24','bgr0','bgra','gbrp','yuvj420p'):
        raise BenchmarkError('UNSUPPORTED_PIXEL_PROFILE')
    if v.get('color_transfer') in ('smpte2084','arib-std-b67'): raise BenchmarkError('HDR_PROFILE_UNSUPPORTED')
    if v.get('sample_aspect_ratio','1:1') not in ('1:1','N/A'): raise BenchmarkError('NONSQUARE_PIXELS_UNSUPPORTED')
    if any(x.get('rotation',0)!=0 for x in v.get('side_data_list',[])) or v.get('tags',{}).get('rotate','0') not in ('0',0):
        raise BenchmarkError('ROTATION_UNSUPPORTED')
    d=fraction(data.get('format',{}).get('duration'))
    if not 0<d<=limits.max_duration_s: raise BenchmarkError('MEDIA_DURATION_LIMIT')
    audio=None
    if aus:
        a=aus[0]
        try: rate=int(a.get('sample_rate',''));channels=a['channels']
        except (ValueError,KeyError,TypeError) as e:raise BenchmarkError('INVALID_AUDIO_METADATA') from e
        integer(rate,1,limits.max_audio_rate);integer(channels,1,limits.max_audio_channels)
        audio={'index':integer(a.get('index'),0,64),'rate':rate,'channels':channels,'codec':a.get('codec_name')}
        if audio['codec'] not in ('aac','opus','vorbis','flac','pcm_s16le','pcm_s24le','pcm_f32le','mp3'):
            raise BenchmarkError('UNSUPPORTED_AUDIO_CODEC')
    formats=data.get('format',{}).get('format_name')
    if type(formats) is not str or not formats or len(formats)>256:raise BenchmarkError('CONTAINER_FORMAT_METADATA_REQUIRED')
    return {'container_formats':formats.split(','),'width':w,'height':h,'fps':str(fps),'duration_s':str(d),'codec':v['codec_name'],
            'pixel_format':v['pix_fmt'],'video_index':integer(v.get('index'),0,64),'audio':audio},command
