from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mimetypes
import os
import subprocess
import sys
from werkzeug.utils import secure_filename
from book_maker.loader import BOOK_LOADER_DICT
from book_maker.translator import MODEL_DICT
from book_maker.utils import LANGUAGES
import logging
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib.epub")

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
CORS(app)

# Configurations
UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Language code mapping
LANGUAGE_CODE_MAPPING = {
    "zh-hans": "CHS",  # Simplified Chinese
    "en": "ENG",       # English
    "ja": "JPN",       # Japanese
    "vi": "VIN",       # Vietnamese
}

def run_image_translation(translated_file_path, image_language):
    """
    Run image translation process using the specified image translator command.
    """
    image_translator_command = [
        "python3", "-m", "image_translator.manga_translator.image_translator",
        "--verbose",
        f"--translator=gpt4omini",
        f"--target-lang={image_language}",  
        f"--input-epub={translated_file_path}",
        f"--input-images=./temp_uploads/images",
        f"--dest=./temp_uploads/images-translated",
        f"--output-images=./temp_uploads/images-translated",
        f"--output-epub={translated_file_path}",
    ]
    logger.debug(f"Running image translation command: {' '.join(image_translator_command)}")
    subprocess.run(image_translator_command, check=True)

@app.route('/api/process', methods=['POST'])
def process_request():
    file = request.files.get('file') or request.form.get('file')
    model = request.form.get('model')
    model_list = request.form.get('selectedModel')
    api_key = request.form.get('apiKey')
    language = request.form.get('language', 'zh-hans')
    single_translate = request.form.get('single_translate')
    text_only = request.form.get('textOnly', 'false').lower() == 'true'

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    if isinstance(file, str):
        filename = os.path.basename(file)
        file_path = file
    else:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    logger.debug(f"File saved at: {file_path}")

    book_type = filename.split('.')[-1]
    if book_type not in BOOK_LOADER_DICT:
        return jsonify({"error": f"Unsupported file type: {book_type}"}), 400

    book_loader = BOOK_LOADER_DICT.get(book_type)
    translate_model = MODEL_DICT.get(model)
    if not translate_model:
        return jsonify({"error": f"Unsupported model: {model}"}), 400

    if language not in LANGUAGES:
        logger.error(f"Unsupported language: {language}")
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    image_language = LANGUAGE_CODE_MAPPING.get(language, "CHS")
    translated_file_path = None  

    try:
        logger.debug(f"Creating book loader with parameters: file_path={file_path}, model={model_list}, language={language}")
        e = book_loader(
            file_path,
            translate_model,
            api_key,
            resume=False,
            language=language,
            model_api_base=None,
            is_test=False,
            test_num=3,
            prompt_config=None,
            single_translate=single_translate,
            context_flag=False,
            temperature=1.0,
        )

        if model in ("openai", "groq"):
            if model_list:
                e.translate_model.set_model_list(model_list.split(","))
            else:
                raise ValueError(
                    "When using openai model, you must also provide --model_list. For default model sets use --model chatgptapi or --model gpt4 or --model gpt4omini",
                )

        logger.debug("Book loader created successfully")
        logger.debug("Starting bilingual book creation")

        e.make_bilingual_book()  # Perform the text translation

        logger.debug("Bilingual book created successfully")

        if not text_only:
            logger.debug("Starting image translation")
            translated_file_path = file_path.replace('.epub', '_bilingual.epub')
            run_image_translation(translated_file_path, image_language)
            logger.debug("Image translation completed successfully")
        else:
            translated_file_path = file_path.replace('.epub', '_bilingual.epub') 

        return jsonify({"message": "Successfully processed file", "translated_file_path": translated_file_path})
    except Exception as ex:
        logger.error(f"Error processing file: {str(ex)}", exc_info=True)
        return jsonify({"error": str(ex)}), 500


@app.route('/api/view-epub/<path:filename>', methods=['GET'])
def view_epub(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not filename.endswith('_bilingual.epub'):
        translated_file_path = file_path.replace('.epub', '_bilingual.epub')
    else:
        translated_file_path = file_path
    
    print("Received filename:", filename)
    print("File path:", file_path)
    print("Translated file path:", translated_file_path)
    
    if not os.path.isfile(translated_file_path):
        print("File not found:", translated_file_path)
        return jsonify({"error": "File not found"}), 404
    
    content_type, _ = mimetypes.guess_type(translated_file_path)
    if not content_type:
        content_type = 'application/epub+zip'

    return send_file(translated_file_path, mimetype=content_type)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
