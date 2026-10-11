"""Services module initialization.

Keep this package lightweight so the app can start without importing every
optional AI dependency at startup.
"""

__all__ = [
    'question_generator',
    'answer_extractor',
    'summarizer',
    'entity_extractor',
    'post_processor'
]


def __getattr__(name):
    if name == 'question_generator':
        from app.services.question_generator import question_generator
        return question_generator
    if name == 'answer_extractor':
        from app.services.answer_extractor import answer_extractor
        return answer_extractor
    if name == 'summarizer':
        from app.services.summarizer import summarizer
        return summarizer
    if name == 'entity_extractor':
        from app.services.entity_extractor import entity_extractor
        return entity_extractor
    if name == 'post_processor':
        from app.services.post_processor import post_processor
        return post_processor
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
