"""Private bounded raster decoder, launched only by visual_assets via H7 isolation."""
import json, sys, warnings
from PIL import Image

def main():
    warnings.simplefilter('error', Image.DecompressionBombWarning)
    Image.MAX_IMAGE_PIXELS = 16_000_000
    with Image.open(sys.argv[1]) as image:
        if image.format not in {'PNG', 'JPEG', 'WEBP'} or getattr(image, 'n_frames', 1) != 1:
            raise ValueError('MEDIA_STATIC_RASTER_REQUIRED')
        if image.width * image.height > 16_000_000:
            raise ValueError('MEDIA_PIXEL_BUDGET')
        if image.getexif().get(274, 1) != 1:
            raise ValueError('MEDIA_EXIF_ORIENTATION_REQUIRES_NORMALIZATION')
        image.load()  # Decode, not merely trust width/height in an envelope.
        result = {'kind': 'image', 'width': image.width, 'height': image.height,
                  'frame_count': 1, 'format': image.format.lower()}
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
