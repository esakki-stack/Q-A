"""App utilities initialization.

Keep these imports lazy so the app can start even when optional document
processing dependencies are not installed yet.
"""

__all__ = [
    'setup_logger',
    'logger',
    'save_upload_file',
    'process_uploaded_file',
    'clean_text',
    'split_sentences',
    'estimate_reading_time',
    'get_word_count'
]


def __getattr__(name):
    if name in {'setup_logger', 'logger'}:
        from app.utils.logger import setup_logger, logger
        return setup_logger if name == 'setup_logger' else logger
    if name in {'save_upload_file', 'process_uploaded_file'}:
        from app.utils.file_handlers import save_upload_file, process_uploaded_file
        return save_upload_file if name == 'save_upload_file' else process_uploaded_file
    if name in {'clean_text', 'split_sentences'}:
        from app.utils.text_cleaner import clean_text, split_sentences
        return clean_text if name == 'clean_text' else split_sentences
    if name in {'estimate_reading_time', 'get_word_count'}:
        from app.utils.helpers import estimate_reading_time, get_word_count
        return estimate_reading_time if name == 'estimate_reading_time' else get_word_count
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
