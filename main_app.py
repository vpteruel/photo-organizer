import os
import exifread
import json
import piexif
import shutil
from ulid import ULID
from datetime import datetime, timezone
from tqdm import tqdm

def get_date(file_path):
    if file_path.lower().endswith('.heic'):
        return None
    with open(file_path, 'rb') as f:
        try:
            # Try to read the date from the file's metadata
            tags = exifread.process_file(f)
            date_tag = tags.get('EXIF DateTimeOriginal')
            if date_tag:
                return datetime.strptime(str(date_tag), '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")

    # Try to read the date from a JSON file with the same name
    json_path = file_path + '.json'
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            timestamp = data.get('photoTakenTime', {}).get('timestamp')
            if timestamp:
                return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)

    # Try to read the date from the file's creation time
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return datetime.strptime(creation_time, '%Y-%m-%dT%H:%M:%S.%fZ')

def set_date(file_path, date):
    if file_path.lower().endswith(('.jpeg', '.jpg', '.png', '.tiff')):
        try:
            exif_dict = piexif.load(file_path)
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date.strftime('%Y:%m:%d %H:%M:%S').encode()
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
        except Exception as e:
            print(f'Error setting date: {e} | {file_path}')

    # Update the file's access and modification times
    os.utime(file_path, (date.timestamp(), date.timestamp()))

def generate_ulid(date):
    if date:
        return ULID.from_timestamp(date.timestamp())
    return ULID()

def copy_and_rename_file(file_path, new_name, dest_dir):
    ext = os.path.splitext(file_path)[1]
    new_path = os.path.join(dest_dir, f'{new_name}{ext}')
    shutil.copy2(file_path, new_path)
    return new_path

def process_files(src_directory, dest_directory):
    for root, _, files in os.walk(src_directory):
        for file in tqdm(files):
            file_path = os.path.join(root, file)
            date = get_date(file_path)
            ulid_instance = generate_ulid(date)
            new_file_path = copy_and_rename_file(file_path, ulid_instance, dest_directory)
            if date:
                set_date(new_file_path, date)

if __name__ == '__main__':
    src_directory = '/home/user/Pictures/source'
    dest_directory = '/home/user/Pictures/target'
    if os.path.exists(dest_directory):
        shutil.rmtree(dest_directory)
    os.makedirs(dest_directory, exist_ok=True)
    process_files(src_directory, dest_directory)
