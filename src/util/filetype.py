def filename_to_file_type(filename: str):
    file_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "svg": "image/svg+xml",
        "avif": "image/avif",
        "js": "text/plain; charset=utf-8" # Not as a script for a reason!
    }

    ending = filename.split(".")[-1]

    return file_types[ending] if ending in file_types else "text/plain"
