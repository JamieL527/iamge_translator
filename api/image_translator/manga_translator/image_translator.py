import os
import asyncio
import logging
import warnings
import argparse
from urllib.parse import unquote
from argparse import ArgumentParser, Namespace
from .manga_translator import MangaTranslator, set_main_logger
from .utils import BASE_PATH, natural_sort
from .extract_images import extract_images_as_png
from .replace_images import replace_images_in_epub
from .save import OUTPUT_FORMATS
from .translators import VALID_LANGUAGES, TRANSLATORS

def url_decode(s):
    s = unquote(s)
    if s.startswith('file:///'):
        s = s[len('file://'):]
    return s

# Additional argparse types
def path(string):
    if not string:
        return ''
    s = url_decode(os.path.expanduser(string))
    if not os.path.exists(s):
        raise argparse.ArgumentTypeError(f'No such file or directory: "{string}"')
    return s

def file_path(string):
    if not string:
        return ''
    s = url_decode(os.path.expanduser(string))
    if not os.path.exists(s):
        raise argparse.ArgumentTypeError(f'No such file: "{string}"')
    return s

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to parse command-line arguments
def parse_args():
    parser = ArgumentParser(description="Pipeline to extract, translate and replace images in EPUB")
    parser.add_argument('--input-epub', type=str, help="Path to the input EPUB file")
    parser.add_argument('--output-epub', type=str, help="Path to save the output EPUB file")
    parser.add_argument('--translator', type=str, choices=TRANSLATORS, help="Translation model to use (e.g., 'gpt3.5')")
    parser.add_argument('--target-lang', type=str, choices=VALID_LANGUAGES, help="Target language for translation")
    parser.add_argument('--input-images', type=str, help="Folder to save extracted images", default=os.path.join(BASE_PATH, 'images'))
    parser.add_argument('--output-images', type=str, help="Folder to save translated images", default=os.path.join(BASE_PATH, 'images-translated'))
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('--mode', type=str, choices=['batch'], default='batch', help="Translation mode")
    parser.add_argument('--pre-dict', type=str, help="Pre-translation dictionary")
    parser.add_argument('--post-dict', type=str, help="Post-translation dictionary")
    parser.add_argument('--dest', type=str, help="Destination folder for translated images")
    parser.add_argument('--kernel-size', type=int, help="Kernel size for translation", default=3)
    parser.add_argument('-f', '--format', default=None, choices=OUTPUT_FORMATS, help='Output format of the translation.')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite already translated images in batch mode.')

    parser.add_argument('--unclip-ratio', default=2.3, type=float, help='How much to extend text skeleton to form bounding box')
    parser.add_argument('--box-threshold', default=0.8, type=float, help='Threshold for bbox generation')
    parser.add_argument('--text-threshold', default=0.85, type=float, help='Threshold for text detection')
    parser.add_argument('--font-size', default=None, type=int, help='Use fixed font size for rendering')
    parser.add_argument('--font-size-offset', default=0, type=int, help='Offset font size by a given amount, positive number increase font size and vice versa')
    parser.add_argument('--font-size-minimum', default=-1, type=int, help='Minimum output font size. Default is image_sides_sum/200')
    parser.add_argument('--font-color', default=None, type=str, help='Overwrite the text fg/bg color detected by the OCR model. Use hex string without the "#" such as FFFFFF for a white foreground or FFFFFF:000000 to also have a black background around the text.')
    parser.add_argument('--font-path', default='', type=file_path, help='Path to font file')
    parser.add_argument('--line-spacing', default=None, type=float, help='Line spacing is font_size * this value. Default is 0.01 for horizontal text and 0.2 for vertical.')

    # Parse arguments and store default values
    parsed_args = parser.parse_args([])
    DEFAULT_ARGS = vars(parsed_args)  # Store the default values

    return parser, DEFAULT_ARGS

# Function to execute the translation pipeline
async def dispatch(args: Namespace):
    # Directly access the args properties
    logger.info(f'Running in {args.mode} mode')

    if args.mode == 'batch':
        if not args.input_images:
            raise Exception('No input image was supplied. Use --input-images <image_path>')

        translator = MangaTranslator(vars(args))

        # Load pre-translation and post-translation dictionaries
        pre_dict = translator.load_dictionary(args.pre_dict)
        post_dict = translator.load_dictionary(args.post_dict)

        dest = args.dest

        # Ignore any warnings related to the images directory processing
        warnings.filterwarnings("ignore", category=UserWarning)

        for path in natural_sort(args.input_images):
            try:
                image_path = os.path.join(args.input_images, path)
                # Apply translation
                await translator.translate_path(image_path, dest, vars(args))

                # Proceed with dictionary application even if textlines are not available
                if hasattr(translator, 'textlines') and translator.textlines:
                    # Apply pre-translation dictionaries to textlines
                    for textline in translator.textlines:
                        textline.text = translator.apply_dictionary(textline.text, pre_dict)
                        logger.info(f'Pre-translation dictionary applied: {textline.text}')

                    # Apply post-translation dictionaries to textlines
                    for textline in translator.textlines:
                        textline.translation = translator.apply_dictionary(textline.translation, post_dict)
                        logger.info(f'Post-translation dictionary applied: {textline.translation}')
                # No warning if textlines is empty or missing, just skip dictionary application.

            except Exception as e:
                # Catch any exception that occurs, but do not stop the process
                logger.debug(f'Error processing {path}: {e}', exc_info=True)  # Log as debug, not error

    else:
        logger.error(f"Mode '{args.mode}' is not supported in this script.")
        raise ValueError(f"Mode '{args.mode}' is not supported.")

# Function to execute the entire pipeline, including image extraction and replacement
async def execute_pipeline(args):
    try:
        # Step 1: Extract images from the EPUB
        images_folder = args.input_images
        logger.info("Step 1: Extracting images from EPUB")
        extract_images_as_png(args.input_epub, images_folder)
        logger.info(f"Images extracted to: {images_folder}")

        # Step 2: Translate the images using the dispatch function
        logger.info("Step 2: Translating images")
        await dispatch(args)

        # Step 3: Replace translated images in the EPUB
        logger.info("Step 3: Replacing images in the EPUB")
        replace_images_in_epub(args.input_epub, args.output_images, args.output_epub)
        logger.info(f"New EPUB created at: {args.output_epub}")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

# Main function to run the pipeline
def main():
    parser, DEFAULT_ARGS = parse_args()
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    try:
        # Run the entire pipeline
        asyncio.run(execute_pipeline(args))

    except KeyboardInterrupt:
        print()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}', exc_info=e if args.verbose else None)

if __name__ == "__main__":
    main()


