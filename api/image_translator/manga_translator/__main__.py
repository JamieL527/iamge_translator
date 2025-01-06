import os
import asyncio
import logging
from argparse import Namespace

from manga_translator.share import MangaShare
from .manga_translator import (
    MangaTranslator,
    set_main_logger,
)
from .args import parser
from .utils import (
    BASE_PATH,
    init_logging,
    get_logger,
    set_log_level,
    natural_sort,
)

async def dispatch(args: Namespace):
    args_dict = vars(args)

    logger.info(f'Running in {args.mode} mode')

    if args.mode == 'batch':
        if not args.input:
            raise Exception('No input image was supplied. Use --input-images <image_path>')
        translator = MangaTranslator(args_dict)

        # Load pre-translation and post-translation dictionaries
        pre_dict = translator.load_dictionary(args.pre_dict)
        post_dict = translator.load_dictionary(args.post_dict)

        dest = args.dest
        for path in natural_sort(args.input): 
            try:
                # Apply translation
                await translator.translate_path(path, dest, args_dict)

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
                logger.error(f'Error processing {path}: {e}')

    else:
        logger.error(f"Mode '{args.mode}' is not supported in this script.")
        raise ValueError(f"Mode '{args.mode}' is not supported.")

if __name__ == '__main__':
    args = None
    init_logging()  # Initialize logging
    try:
        args = parser.parse_args()  # Parse command-line arguments
        set_log_level(level=logging.DEBUG if args.verbose else logging.INFO)  # Set log level
        logger = get_logger(args.mode)  # Get logger
        set_main_logger(logger)  # Set the logger for the main module
        if args.mode != 'web':
            logger.debug(args)

        # Run the dispatch function
        asyncio.run(dispatch(args))

    except KeyboardInterrupt:
        if not args or args.mode != 'web':
            print()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}',
                     exc_info=e if args and args.verbose else None)
