import os
import zipfile
import shutil
from shutil import rmtree
from tqdm import tqdm

def replace_images_in_epub(original_epub, translated_images_folder, output_epub):
    """
    Replace images in an EPUB file if corresponding translated images exist, otherwise keep the original images.
    :param original_epub: Path to the original EPUB file.
    :param translated_images_folder: Folder containing translated images.
    :param output_epub: Path to the output EPUB file.
    """
    # Step 1: Define temporary folder for extraction
    temp_folder = 'temp_epub'

    # Clean up any pre-existing temp folder
    if os.path.exists(temp_folder):
        rmtree(temp_folder)

    # Step 2: Extract the original EPUB to the temporary folder
    with zipfile.ZipFile(original_epub, 'r') as epub_zip:
        epub_zip.extractall(temp_folder)

    # Step 3: Collect all image files
    image_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(temp_folder)
        for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
    ]

    replaced_count = 0
    skipped_count = 0

    # Step 4: Replace images with progress bar
    for file_path in tqdm(image_files, desc="Processing images"):
        file_name = os.path.basename(file_path)
        translated_image_path = os.path.join(translated_images_folder, file_name)

        if os.path.exists(translated_image_path):
            shutil.copy(translated_image_path, file_path)
            replaced_count += 1
        else:
            skipped_count += 1

    # Step 5: Repackage the EPUB
    with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
        for root, _, files in os.walk(temp_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_folder)  # Maintain relative path
                epub_zip.write(file_path, arcname)

    # Clean up the temporary folder
    rmtree(temp_folder)

    # Final summary
    print(f"Replacement completed: {replaced_count} images replaced, {skipped_count} images kept original.")
    print(f"New EPUB created at: {output_epub}")
