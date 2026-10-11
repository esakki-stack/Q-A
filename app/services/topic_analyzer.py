"""Topic Analyzer Service - Extract themes, topics, and insights"""
from typing import Dict, List, Any
from app.utils.logger import logger
import re
from collections import Counter

class TopicAnalyzer:
    """Analyze articles for main themes, topics, and key insights"""
    
    def __init__(self):
        self.topic_keywords = {
            'politics': {
                'keywords': ['election', 'political', 'government', 'president', 'minister', 'parliament', 'congress', 'vote', 'senator', 'representative', 'legislation', 'bill', 'senator', 'campaign', 'democracy'],
                'weight': 1.0
            },
            'economics': {
                'keywords': ['economy', 'economic', 'market', 'stock', 'trade', 'business', 'financial', 'gdp', 'inflation', 'recession', 'investment', 'commodity', 'price', 'profit', 'revenue'],
                'weight': 1.0
            },
            'science_technology': {
                'keywords': ['research', 'study', 'scientist', 'discovered', 'technology', 'innovation', 'breakthrough', 'algorithm', 'ai', 'machine learning', 'experiment', 'data', 'analysis', 'quantum', 'tech'],
                'weight': 1.0
            },
            'health_medicine': {
                'keywords': ['health', 'disease', 'pandemic', 'vaccine', 'medical', 'hospital', 'patient', 'treatment', 'clinical', 'drug', 'virus', 'infection', 'doctor', 'medicine', 'epidemic'],
                'weight': 1.0
            },
            'law_justice': {
                'keywords': ['court', 'legal', 'law', 'judge', 'verdict', 'trial', 'lawsuit', 'attorney', 'crime', 'criminal', 'conviction', 'sentence', 'justice', 'regulation'],
                'weight': 1.0
            },
            'environment': {
                'keywords': ['climate', 'environmental', 'pollution', 'green', 'renewable', 'carbon', 'weather', 'conservation', 'sustainable', 'global warming', 'emissions', 'energy', 'nature'],
                'weight': 1.0
            },
            'society_culture': {
                'keywords': ['social', 'community', 'public', 'culture', 'education', 'diversity', 'rights', 'protest', 'movement', 'society', 'tradition', 'identity', 'social media'],
                'weight': 1.0
            },
            'conflict_crisis': {
                'keywords': ['war', 'military', 'conflict', 'attack', 'defense', 'crisis', 'emergency', 'disaster', 'violence', 'bombing', 'terrorism', 'security', 'threat'],
                'weight': 1.0
            },
            'business_industry': {
                'keywords': ['company', 'corporation', 'industry', 'startup', 'entrepreneur', 'ceo', 'management', 'merger', 'acquisition', 'employee', 'production', 'manufacturing', 'supply chain'],
                'weight': 0.9
            },
            'sports': {
                'keywords': ['sports', 'game', 'player', 'team', 'coach', 'match', 'championship', 'league', 'tournament', 'coach', 'victory', 'defeat', 'athlete'],
                'weight': 0.8
            }
        }
        
        self.issue_categories = {
            'policy_change': ['new policy', 'new law', 'regulation', 'executive order', 'amendment'],
            'investigation': ['investigation', 'inquiry', 'probe', 'scandal', 'lawsuit', 'expose'],
            'disaster': ['disaster', 'emergency', 'crisis', 'accident', 'catastrophe', 'tragedy'],
            'discovery': ['discover', 'find', 'breakthrough', 'new research', 'found'],
            'conflict': ['war', 'military action', 'attack', 'conflict', 'confrontation'],
            'economic': ['market', 'trade', 'financial', 'economic', 'investment', 'business'],
            'social': ['protest', 'movement', 'community', 'social', 'rights', 'diversity'],
            'appointment': ['appoint', 'hire', 'elect', 'promote', 'announce leadership'],
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Comprehensive topic analysis of article"""
        analysis = {
            'primary_topic': None,
            'secondary_topics': [],
            'identified_themes': [],
            'issue_category': None,
            'affected_groups': [],
            'geographic_scope': None,
            'time_sensitivity': None,
            'key_insights': [],
            'article_tone': None
        }
        
        try:
            # Identify primary and secondary topics
            topics = self._identify_topics(text)
            if topics:
                analysis['primary_topic'] = topics[0]
                analysis['secondary_topics'] = topics[1:3] if len(topics) > 1 else []
            
            # Identify themes
            analysis['identified_themes'] = self._identify_themes(text)
            
            # Categorize issue
            analysis['issue_category'] = self._categorize_issue(text)
            
            # Identify affected groups
            analysis['affected_groups'] = self._identify_affected_groups(text)
            
            # Determine geographic scope
            analysis['geographic_scope'] = self._identify_geographic_scope(text)
            
            # Assess time sensitivity
            analysis['time_sensitivity'] = self._assess_time_sensitivity(text)
            
            # Extract key insights
            analysis['key_insights'] = self._extract_insights(text)
            
            # Analyze tone
            analysis['article_tone'] = self._analyze_tone(text)
            
        except Exception as e:
            logger.error(f"Error analyzing topics: {str(e)}")
        
        return analysis
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identify primary and secondary topics"""
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, config in self.topic_keywords.items():
            score = 0
            for keyword in config['keywords']:
                # Count occurrences of keyword
                pattern = rf'\b{keyword}\b'
                matches = len(re.findall(pattern, text_lower))
                score += matches * config['weight']
            
            if score > 0:
                topic_scores[topic] = score
        
        # Sort by score and return top topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, score in sorted_topics[:3]]
    
    def _identify_themes(self, text: str) -> List[str]:
        """Identify underlying themes in article"""
        themes = []
        text_lower = text.lower()
        
        theme_patterns = {
            'accountability': ['responsible', 'accountability', 'investigate', 'oversight', 'transparent'],
            'innovation': ['new', 'breakthrough', 'innovative', 'cutting-edge', 'revolution'],
            'crisis_management': ['emergency', 'response', 'crisis', 'disaster', 'recovery'],
            'inequality': ['inequality', 'disparity', 'discrimination', 'unfair', 'disadvantaged'],
            'sustainability': ['sustainable', 'green', 'environmental', 'conservation', 'renewable'],
            'transformation': ['transform', 'change', 'shift', 'evolution', 'modernize'],
            'opportunity': ['opportunity', 'potential', 'growth', 'expansion', 'develop'],
            'risk': ['risk', 'threat', 'danger', 'concern', 'challenge'],
        }
        
        for theme, keywords in theme_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        return themes[:5]
    
    def _categorize_issue(self, text: str) -> str:
        """Categorize the type of issue in article"""
        text_lower = text.lower()
        
        for category, keywords in self.issue_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general_news'
    
    def _identify_affected_groups(self, text: str) -> List[str]:
        """Identify groups affected by the issue"""
        affected_groups = []
        
        group_patterns = {
            'general_public': ['public', 'people', 'citizens', 'population', 'everyone'],
            'investors': ['investor', 'shareholder', 'stockholder', 'market', 'financial'],
            'workers_employees': ['worker', 'employee', 'labor', 'union', 'staff'],
            'government': ['government', 'state', 'federal', 'official', 'administration'],
            'business_sector': ['business', 'company', 'enterprise', 'industry', 'corporation'],
            'students_youth': ['student', 'youth', 'young', 'school', 'university', 'education'],
            'healthcare': ['patient', 'doctor', 'hospital', 'health', 'medical', 'healthcare'],
            'environment': ['environment', 'climate', 'nature', 'wildlife', 'ecosystem'],
        }
        
        text_lower = text.lower()
        
        for group, keywords in group_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                affected_groups.append(group)
        
        return affected_groups[:4]
    
    def _identify_geographic_scope(self, text: str) -> str:
        """Determine geographic scope of story"""
        text_lower = text.lower()
        
        if any(country in text_lower for country in ['united states', 'us', 'usa', 'america', 'american']):
            if any(word in text_lower for word in ['global', 'world', 'international', 'worldwide']):
                return 'global_with_us_focus'
            return 'united_states'
        
        elif any(region in text_lower for region in ['europe', 'asia', 'africa', 'latin america', 'middle east']):
            if any(word in text_lower for word in ['global', 'world', 'international']):
                return 'global'
            return 'regional'
        
        elif any(word in text_lower for word in ['global', 'world', 'international', 'worldwide']):
            return 'global'
        
        elif any(word in text_lower for word in ['local', 'city', 'county', 'state']):
            return 'local'
        
        return 'unspecified'
    
    def _assess_time_sensitivity(self, text: str) -> str:
        """Assess how time-sensitive the news is"""
        text_lower = text.lower()
        
        breaking_indicators = [
            'just', 'today', 'breaking', 'developing', 'just announced',
            'minutes ago', 'hours ago', 'last night', 'early today',
            'emergency', 'urgent', 'immediate'
        ]
        
        ongoing_indicators = [
            'ongoing', 'continuing', 'continues', 'latest', 'update',
            'developments', 'unfolding', 'as the situation develops'
        ]
        
        if any(indicator in text_lower for indicator in breaking_indicators):
            return 'breaking'
        elif any(indicator in text_lower for indicator in ongoing_indicators):
            return 'ongoing'
        else:
            return 'standard'
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from article"""
        insights = []
        
        # Look for insight indicators
        insight_patterns = [
            r'(?:this means|this indicates|suggests that|implies that|reveals that|shows that|demonstrates that)(.*?)(?:\.|[.!?])',
            r'(?:key insight|important point|critical|essential)(.*?)(?:\.|[.!?])',
            r'(?:according to|data shows|research indicates|evidence suggests)(.*?)(?:\.|[.!?])',
        ]
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            insights.extend([match.strip() for match in matches[:2]])
        
        return insights[:3]
    
    def _analyze_tone(self, text: str) -> str:
        """Analyze the tone of the article"""
        text_lower = text.lower()
        
        positive_indicators = ['success', 'victory', 'achievement', 'triumph', 'progress', 'benefit', 'positive']
        negative_indicators = ['crisis', 'disaster', 'failure', 'loss', 'challenge', 'concern', 'risk', 'problem']
        neutral_indicators = ['report', 'found', 'indicated', 'suggest', 'according', 'analysis']
        
        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def generate_article_brief(self, analysis: Dict[str, Any]) -> str:
        """Generate a brief summary of article analysis"""
        brief_parts = []
        
        if analysis['primary_topic']:
            brief_parts.append(f"Topic: {analysis['primary_topic'].replace('_', ' ').title()}")
        
        if analysis['issue_category']:
            brief_parts.append(f"Type: {analysis['issue_category'].replace('_', ' ').title()}")
        
        if analysis['affected_groups']:
            brief_parts.append(f"Affects: {', '.join([g.replace('_', ' ').title() for g in analysis['affected_groups'][:2]])}")
        
        if analysis['geographic_scope']:
            brief_parts.append(f"Scope: {analysis['geographic_scope'].replace('_', ' ').title()}")
        
        if analysis['time_sensitivity']:
            brief_parts.append(f"Urgency: {analysis['time_sensitivity'].title()}")
        
        return " | ".join(brief_parts)
