"""Export Service - Generate Q&A in multiple formats"""
from typing import Dict, List, Any
from app.utils.logger import logger
from app.models.qa_models import QAResponse
import json
from datetime import datetime
import html

class ExportService:
    """Export Q&A pairs in various formats for newsroom use"""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
    
    def export_to_json(self, response: QAResponse, include_metadata: bool = True) -> str:
        """Export Q&A pairs to JSON for CMS integration"""
        try:
            data = {
                'format': 'json',
                'generated_at': self.timestamp,
                'article_info': {
                    'title': response.article_info.title,
                    'word_count': response.article_info.word_count,
                    'reading_time_minutes': response.article_info.reading_time_minutes,
                },
                'qa_pairs': [
                    {
                        'id': idx + 1,
                        'question': pair.question,
                        'answer': pair.answer,
                        'confidence': pair.confidence,
                        'difficulty': pair.difficulty,
                        'question_type': pair.question_type,
                    }
                    for idx, pair in enumerate(response.qa_pairs)
                ],
                'statistics': {
                    'total_questions': len(response.qa_pairs),
                    'average_confidence': round(sum(p.confidence for p in response.qa_pairs) / len(response.qa_pairs) if response.qa_pairs else 0, 3),
                    'processing_time': response.processing_time,
                }
            }
            
            if include_metadata:
                data['metadata'] = {
                    'key_entities': response.key_entities,
                    'timeline_events': [
                        {
                            'date': str(event.get('dates', [])),
                            'event': event.get('event_text', ''),
                            'actions': event.get('actions', [])
                        }
                        for event in response.timeline_events[:5]
                    ],
                    'summary': response.summary,
                }
            
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return json.dumps({'error': str(e)})
    
    def export_to_markdown(self, response: QAResponse, include_summary: bool = True) -> str:
        """Export Q&A pairs to Markdown for newsletters and web content"""
        try:
            content = []
            
            # Header
            if response.article_info.title:
                content.append(f"# {response.article_info.title}")
            else:
                content.append("# Q&A Explainer")
            
            content.append("")
            content.append(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*")
            content.append("")
            
            # Summary section
            if include_summary and response.summary:
                content.append("## Summary")
                content.append(response.summary)
                content.append("")
            
            # Key Facts
            if response.key_entities:
                content.append("## Key Facts")
                if response.key_entities.get('persons'):
                    content.append(f"**People Involved:** {', '.join(response.key_entities['persons'][:5])}")
                if response.key_entities.get('organizations'):
                    content.append(f"**Organizations:** {', '.join(response.key_entities['organizations'][:5])}")
                if response.key_entities.get('locations'):
                    content.append(f"**Locations:** {', '.join(response.key_entities['locations'][:5])}")
                content.append("")
            
            # Q&A Section
            content.append("## Questions & Answers")
            content.append("")
            
            for idx, pair in enumerate(response.qa_pairs, 1):
                content.append(f"### {idx}. {pair.question}")
                content.append(f"**Confidence:** {pair.confidence:.1%}")
                content.append("")
                content.append(pair.answer)
                content.append("")
            
            # Stats
            content.append("---")
            content.append("## Statistics")
            avg_confidence = sum(p.confidence for p in response.qa_pairs) / len(response.qa_pairs) if response.qa_pairs else 0
            content.append(f"- **Total Q&A Pairs:** {len(response.qa_pairs)}")
            content.append(f"- **Average Confidence:** {avg_confidence:.1%}")
            content.append(f"- **Processing Time:** {response.processing_time:.2f}s")
            content.append(f"- **Article Word Count:** {response.article_info.word_count}")
            
            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {str(e)}")
            return f"Error: {str(e)}"
    
    def export_to_html(self, response: QAResponse, include_css: bool = True) -> str:
        """Export Q&A pairs to HTML for web publishing"""
        try:
            html_content = []
            
            if include_css:
                html_content.append(self._get_html_styles())
            
            html_content.append("<body>")
            html_content.append('<div class="qa-container">')
            
            # Header
            if response.article_info.title:
                html_content.append(f'<h1 class="qa-title">{html.escape(response.article_info.title)}</h1>')
            
            html_content.append(f'<p class="qa-meta">Generated: {datetime.now().strftime("%B %d, %Y")}</p>')
            
            # Summary
            if response.summary:
                html_content.append('<div class="qa-summary">')
                html_content.append('<h2>Summary</h2>')
                html_content.append(f'<p>{html.escape(response.summary)}</p>')
                html_content.append('</div>')
            
            # Key Entities
            if response.key_entities:
                html_content.append('<div class="qa-facts">')
                html_content.append('<h2>Key Facts</h2>')
                html_content.append('<ul>')
                if response.key_entities.get('persons'):
                    html_content.append(f"<li><strong>People:</strong> {', '.join(response.key_entities['persons'][:5])}</li>")
                if response.key_entities.get('organizations'):
                    html_content.append(f"<li><strong>Organizations:</strong> {', '.join(response.key_entities['organizations'][:5])}</li>")
                if response.key_entities.get('locations'):
                    html_content.append(f"<li><strong>Locations:</strong> {', '.join(response.key_entities['locations'][:5])}</li>")
                html_content.append('</ul>')
                html_content.append('</div>')
            
            # Q&A Pairs
            html_content.append('<div class="qa-pairs">')
            html_content.append('<h2>Questions & Answers</h2>')
            
            for idx, pair in enumerate(response.qa_pairs, 1):
                html_content.append('<div class="qa-item">')
                html_content.append(f'<div class="qa-number">Q{idx}</div>')
                html_content.append(f'<h3 class="qa-question">{html.escape(pair.question)}</h3>')
                html_content.append(f'<div class="qa-confidence">Confidence: {pair.confidence:.1%}</div>')
                html_content.append(f'<p class="qa-answer">{html.escape(pair.answer)}</p>')
                html_content.append('</div>')
            
            html_content.append('</div>')
            
            # Stats
            avg_confidence = sum(p.confidence for p in response.qa_pairs) / len(response.qa_pairs) if response.qa_pairs else 0
            html_content.append('<div class="qa-stats">')
            html_content.append('<h2>Statistics</h2>')
            html_content.append(f'<p>Total Q&A Pairs: <strong>{len(response.qa_pairs)}</strong></p>')
            html_content.append(f'<p>Average Confidence: <strong>{avg_confidence:.1%}</strong></p>')
            html_content.append(f'<p>Processing Time: <strong>{response.processing_time:.2f}s</strong></p>')
            html_content.append('</div>')
            
            html_content.append('</div>')
            html_content.append('</body>')
            
            return "\n".join(html_content)
        except Exception as e:
            logger.error(f"Error exporting to HTML: {str(e)}")
            return f"<p>Error: {str(e)}</p>"
    
    def export_to_cms_json(self, response: QAResponse) -> str:
        """Export to standard CMS JSON format (Wordpress, Contentful, etc.)"""
        try:
            cms_data = {
                'type': 'qa_explainer',
                'title': response.article_info.title or 'Q&A Explainer',
                'content': self._build_cms_content(response),
                'metadata': {
                    'author': response.article_info.author,
                    'publish_date': response.article_info.publish_date.isoformat() if response.article_info.publish_date else None,
                    'updated_date': datetime.now().isoformat(),
                    'word_count': response.article_info.word_count,
                    'reading_time': int(response.article_info.reading_time_minutes),
                    'language': response.article_info.language,
                },
                'categories': response.article_info.categories,
                'acf': {  # Advanced Custom Fields format for WordPress
                    'qa_pairs': [
                        {
                            'q': pair.question,
                            'a': pair.answer,
                            'confidence_score': pair.confidence,
                            'difficulty_level': pair.difficulty,
                        }
                        for pair in response.qa_pairs
                    ],
                    'summary': response.summary,
                    'key_entities': response.key_entities,
                }
            }
            
            return json.dumps(cms_data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error exporting to CMS JSON: {str(e)}")
            return json.dumps({'error': str(e)})
    
    def export_for_social_media(self, response: QAResponse, max_chars: int = 280) -> List[str]:
        """Generate social media snippets from Q&A pairs"""
        try:
            snippets = []
            
            # Twitter/X style posts
            for idx, pair in enumerate(response.qa_pairs[:5], 1):
                snippet = f"Q{idx}: {pair.question}\n\nA: {pair.answer[:150]}..."
                if len(snippet) <= max_chars:
                    snippets.append(snippet)
                else:
                    # Truncate to fit
                    truncated = f"Q{idx}: {pair.question}\n\nA: {pair.answer[:100]}..."
                    snippets.append(truncated[:max_chars])
            
            return snippets
        except Exception as e:
            logger.error(f"Error exporting for social media: {str(e)}")
            return []
    
    @staticmethod
    def _get_html_styles() -> str:
        """Get embedded CSS styles for HTML export"""
        return """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            
            .qa-container {
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .qa-title {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 10px;
            }
            
            .qa-meta {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
            
            .qa-summary, .qa-facts {
                background: #ecf0f1;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin-bottom: 20px;
                border-radius: 4px;
            }
            
            .qa-item {
                margin-bottom: 25px;
                padding: 15px;
                background: #f9f9f9;
                border-radius: 4px;
                border-left: 4px solid #2ecc71;
            }
            
            .qa-number {
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .qa-question {
                color: #2c3e50;
                margin: 8px 0;
            }
            
            .qa-confidence {
                color: #27ae60;
                font-size: 0.9em;
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .qa-answer {
                color: #555;
                line-height: 1.7;
            }
            
            .qa-stats {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 4px;
                margin-top: 30px;
            }
            
            h2 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 20px;
            }
            
            ul {
                margin: 10px 0;
                padding-left: 20px;
            }
        </style>
        """
    
    @staticmethod
    def _build_cms_content(response: QAResponse) -> str:
        """Build content block for CMS"""
        blocks = []
        
        if response.summary:
            blocks.append(f"<h2>Summary</h2><p>{response.summary}</p>")
        
        blocks.append("<h2>Questions & Answers</h2>")
        for idx, pair in enumerate(response.qa_pairs, 1):
            blocks.append(f"<h3>Q{idx}: {pair.question}</h3>")
            blocks.append(f"<p>{pair.answer}</p>")
        
        return "".join(blocks)
