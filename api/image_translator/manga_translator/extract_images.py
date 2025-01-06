import os
from ebooklib import epub
from ebooklib import ITEM_IMAGE, ITEM_DOCUMENT
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from tqdm import tqdm
from bs4 import BeautifulSoup

def extract_images_as_png(epub_path, output_dir):
    """
    Extract images from an ePUB file, including accurately identifying the cover image, and save them in PNG format.

    :param epub_path: Path to the ePUB file.
    :param output_dir: Directory to save the extracted images.
    """
    # Open the ePUB file
    book = epub.read_epub(epub_path)

    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Check all metadata to locate the cover image ID
    cover_id = None
    for metadata in book.metadata.values():
        for meta in metadata:
            if isinstance(meta, dict) and meta.get("name", "").lower() == "cover":
                cover_id = meta.get("content")
                break
        if cover_id:
            break

    # Attempt to extract the cover image using the cover ID
    cover_extracted = False
    if cover_id:
        for item in book.get_items():
            if item.id == cover_id and item.get_type() == ITEM_IMAGE:
                try:
                    cover_data = item.get_content()
                    cover_path = os.path.join(output_dir, "cover.png")
                    with Image.open(BytesIO(cover_data)) as cover_image:
                        cover_image.save(cover_path, format="PNG")
                    print(f"Cover image saved as: {cover_path}")
                    cover_extracted = True
                    break
                except Exception as e:
                    print(f"Error extracting cover image from metadata: {e}")

    # If the cover image is not extracted, attempt to parse it from HTML pages
    if not cover_extracted:
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                img_tag = soup.find("img")
                if img_tag and "src" in img_tag.attrs:
                    img_src = img_tag["src"]
                    for img_item in book.get_items():
                        if img_item.file_name.endswith(img_src):
                            try:
                                cover_data = img_item.get_content()
                                cover_path = os.path.join(output_dir, "cover.png")
                                with Image.open(BytesIO(cover_data)) as cover_image:
                                    cover_image.save(cover_path, format="PNG")
                                print(f"Cover image saved as: {cover_path}")
                                cover_extracted = True
                                break
                            except Exception as e:
                                print(f"Error parsing cover image from HTML: {e}")
            if cover_extracted:
                break

    if not cover_extracted:
        print("Cover image not found or failed to extract.")

    # Extract other images from the ePUB file
    image_items = [item for item in book.get_items() if item.get_type() == ITEM_IMAGE]

    # Use tqdm to display progress
    with tqdm(total=len(image_items), desc="Extracting images", unit="image") as progress_bar:
        for item in image_items:
            image_data = item.get_content()  # Get image content
            file_name = os.path.basename(item.file_name)  # Extract the file name
            base_filename, _ = os.path.splitext(file_name)
            image_filename = os.path.join(output_dir, base_filename + ".png")

            try:
                # Read the image using Pillow
                image = Image.open(BytesIO(image_data))

                # Convert and save as PNG
                image.save(image_filename, format="PNG")
            except UnidentifiedImageError:
                print(f"Skipping unsupported image format: {file_name}")
            except Exception as e:
                print(f"Error processing image {file_name}: {e}")

            # Update the progress bar
            progress_bar.update(1)

    # Print summary after extraction
    print(f"\nExtraction complete: {len(image_items)} images extracted and saved to '{output_dir}'.")