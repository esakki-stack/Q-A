"""Stakeholder and Timeline Extractor Service"""
from typing import List, Dict, Any, Tuple
from app.utils.logger import logger
import re
from datetime import datetime

class StakeholderTimelineExtractor:
    """Extract stakeholders, timeline events, and key outcomes from articles"""
    
    def __init__(self):
        self.date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s+\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b(?:today|yesterday|tomorrow|last\s+\w+|next\s+\w+|this\s+\w+)\b',
        ]
        
        self.action_verbs = [
            'announced', 'declared', 'said', 'confirmed', 'revealed', 'reported',
            'stated', 'claimed', 'released', 'issued', 'proposed', 'demanded',
            'requested', 'approved', 'rejected', 'suspended', 'halted', 'launched',
            'dismissed', 'terminated', 'appointed', 'elected', 'passed', 'signed',
            'vetoed', 'convicted', 'acquitted', 'arrested', 'charged'
        ]
        
        self.stakeholder_indicators = [
            'government', 'ministry', 'department', 'agency', 'official',
            'spokesman', 'spokeswoman', 'president', 'minister', 'senator',
            'representative', 'judge', 'court', 'parliament', 'congress',
            'company', 'corporation', 'industry', 'organization', 'association',
            'group', 'party', 'union', 'leader', 'director', 'ceo', 'founder'
        ]
    
    def extract_timeline(self, text: str) -> List[Dict[str, Any]]:
        """Extract timeline events from article text"""
        events = []
        sentences = re.split(r'[.!?]+', text)
        
        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Extract dates
            dates = self._extract_dates(sentence)
            
            # Extract actions
            actions = self._extract_actions(sentence)
            
            if dates or actions:
                event = {
                    'event_text': sentence,
                    'paragraph_index': idx,
                    'dates': dates,
                    'actions': actions,
                    'entities': self._extract_entities_from_sentence(sentence)
                }
                events.append(event)
        
        # Sort by date if possible
        events = self._sort_timeline_events(events)
        return events[:20]  # Return top 20 events
    
    def extract_stakeholders(self, text: str) -> Dict[str, List[str]]:
        """Extract key stakeholders, organizations, and people"""
        stakeholders = {
            'individuals': [],
            'organizations': [],
            'government_bodies': [],
            'private_sector': [],
            'civil_society': []
        }
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Extract proper nouns (capitalized words)
            proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', sentence)
            
            for noun in proper_nouns:
                if self._is_person_name(noun):
                    if noun not in stakeholders['individuals']:
                        stakeholders['individuals'].append(noun)
                elif self._is_government_body(noun):
                    if noun not in stakeholders['government_bodies']:
                        stakeholders['government_bodies'].append(noun)
                elif self._is_organization(noun, sentence):
                    if noun not in stakeholders['organizations']:
                        stakeholders['organizations'].append(noun)
        
        # Clean and limit results
        for key in stakeholders:
            stakeholders[key] = list(dict.fromkeys(stakeholders[key]))[:10]  # Remove duplicates and limit
        
        return stakeholders
    
    def extract_key_outcomes(self, text: str) -> List[Dict[str, str]]:
        """Extract key outcomes, decisions, and results"""
        outcomes = []
        sentences = re.split(r'[.!?]+', text)
        
        outcome_keywords = [
            'resulted in', 'led to', 'caused', 'impact', 'consequence',
            'outcome', 'conclusion', 'decision', 'verdict', 'ruling',
            'approved', 'rejected', 'passed', 'failed', 'succeeded',
            'won', 'lost', 'achieved', 'failed', 'will be', 'is expected'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Check if sentence contains outcome keywords
            if any(keyword in sentence.lower() for keyword in outcome_keywords):
                outcomes.append({
                    'outcome': sentence,
                    'type': self._classify_outcome(sentence)
                })
        
        return outcomes[:15]
    
    def extract_key_topics_themes(self, text: str) -> Dict[str, List[str]]:
        """Extract main themes and topics from article"""
        themes = {
            'primary_topic': None,
            'secondary_topics': [],
            'issue_categories': [],
            'affected_sectors': []
        }
        
        # Analyze first few sentences for main topic
        sentences = re.split(r'[.!?]+', text)[:5]
        main_text = ' '.join(sentences)
        
        # Topic keywords mapping
        topic_keywords = {
            'politics': ['election', 'political', 'government', 'president', 'minister', 'parliament', 'congress', 'vote'],
            'economics': ['economy', 'economic', 'market', 'stock', 'trade', 'business', 'financial', 'gdp'],
            'science': ['research', 'study', 'scientist', 'discovered', 'technology', 'innovation', 'breakthrough'],
            'health': ['health', 'disease', 'pandemic', 'vaccine', 'medical', 'hospital', 'patient', 'treatment'],
            'law': ['court', 'legal', 'law', 'judge', 'verdict', 'trial', 'lawsuit', 'attorney'],
            'environment': ['climate', 'environmental', 'pollution', 'green', 'renewable', 'carbon', 'weather'],
            'society': ['social', 'community', 'public', 'culture', 'education', 'diversity', 'rights'],
            'conflict': ['war', 'military', 'conflict', 'attack', 'defense', 'crisis', 'emergency']
        }
        
        for topic, keywords in topic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in main_text.lower())
            if matches > 0:
                if not themes['primary_topic']:
                    themes['primary_topic'] = topic
                themes['secondary_topics'].append((topic, matches))
        
        # Sort secondary topics by relevance
        themes['secondary_topics'] = [t[0] for t in sorted(themes['secondary_topics'], key=lambda x: x[1], reverse=True)]
        
        return themes
    
    def _extract_dates(self, sentence: str) -> List[str]:
        """Extract date patterns from sentence"""
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            dates.extend(matches)
        return list(dict.fromkeys(dates))  # Remove duplicates
    
    def _extract_actions(self, sentence: str) -> List[str]:
        """Extract action verbs from sentence"""
        actions = []
        for verb in self.action_verbs:
            if re.search(rf'\b{verb}\b', sentence, re.IGNORECASE):
                actions.append(verb)
        return actions
    
    def _extract_entities_from_sentence(self, sentence: str) -> Dict[str, List[str]]:
        """Extract entities mentioned in sentence"""
        entities = {
            'people': [],
            'organizations': [],
            'locations': []
        }
        
        # Simple heuristic-based extraction
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', sentence)
        
        for noun in proper_nouns[:3]:
            if self._is_person_name(noun):
                entities['people'].append(noun)
            elif self._is_organization(noun, sentence):
                entities['organizations'].append(noun)
            elif self._is_location(noun):
                entities['locations'].append(noun)
        
        return entities
    
    @staticmethod
    def _is_person_name(word: str) -> bool:
        """Heuristic to identify if word is likely a person's name"""
        common_titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'judge', 'general', 'admiral']
        common_suffixes = ['jr', 'sr', 'iii', 'iv', 'ph.d', 'esq']
        
        # Check for common name patterns
        if any(title in word.lower() for title in common_titles):
            return True
        
        # Check word length and capitalization
        if len(word) > 2 and word[0].isupper():
            return True
        
        return False
    
    @staticmethod
    def _is_organization(word: str, context: str) -> bool:
        """Heuristic to identify if word is an organization"""
        org_suffixes = ['inc', 'ltd', 'corp', 'llc', 'gmbh', 'sa', 'ag', 'plc']
        org_keywords = ['company', 'corporation', 'organization', 'foundation', 'institute']
        
        word_lower = word.lower()
        
        if any(word_lower.endswith(suffix) for suffix in org_suffixes):
            return True
        
        if any(keyword in context.lower() for keyword in org_keywords):
            return True
        
        return False
    
    @staticmethod
    def _is_location(word: str) -> bool:
        """Heuristic to identify if word is a location"""
        common_locations = [
            'united states', 'california', 'texas', 'new york', 'london', 'paris',
            'japan', 'china', 'india', 'germany', 'france', 'russia', 'brazil',
            'africa', 'europe', 'asia', 'america', 'australia', 'middle east'
        ]
        
        return any(loc.lower() in word.lower() for loc in common_locations)
    
    @staticmethod
    def _sort_timeline_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort timeline events chronologically"""
        # Sort by paragraph index to maintain document order
        return sorted(events, key=lambda x: x['paragraph_index'])
    
    @staticmethod
    def _classify_outcome(text: str) -> str:
        """Classify the type of outcome"""
        if any(word in text.lower() for word in ['approved', 'passed', 'succeeded', 'won', 'achieved']):
            return 'positive'
        elif any(word in text.lower() for word in ['rejected', 'failed', 'lost', 'denied']):
            return 'negative'
        elif any(word in text.lower() for word in ['suspended', 'halted', 'delayed', 'postponed']):
            return 'neutral'
        else:
            return 'mixed'
