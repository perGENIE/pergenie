def clean_file_name(file_name, file_format):
    return file_name.replace('.', '_').replace(' ', '_') + '.' + file_format
