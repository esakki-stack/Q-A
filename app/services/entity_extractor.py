"""Entity Extractor Service"""
from typing import List, Dict, Any
from app.utils.logger import logger
import re

class EntityExtractor:
    """Extract named entities from text"""
    
    def __init__(self):
        self.person_titles = ['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.', 'CEO', 'President', 'King', 'Queen']
        self.organization_keywords = ['Inc.', 'Ltd.', 'Corp.', 'Company', 'University', 'Bank', 'Government']
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        try:
            entities = {
                "persons": self._extract_persons(text),
                "organizations": self._extract_organizations(text),
                "locations": self._extract_locations(text),
                "miscellaneous": self._extract_miscellaneous(text)
            }
            
            logger.info(f"Extracted {sum(len(v) for v in entities.values())} entities")
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {
                "persons": [],
                "organizations": [],
                "locations": [],
                "miscellaneous": []
            }
    
    def _extract_persons(self, text: str) -> List[str]:
        """Extract person names"""
        persons = set()
        
        # Look for title patterns
        for title in self.person_titles:
            pattern = f'{title}\\s+([A-Z][a-z]+\\s+[A-Z][a-z]+)'
            matches = re.findall(pattern, text)
            persons.update(matches)
        
        # Look for capitalized words (simple heuristic)
        pattern = r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b'
        matches = re.findall(pattern, text)
        persons.update([f'{f} {l}' for f, l in matches])
        
        return list(persons)[:10]
    
    def _extract_organizations(self, text: str) -> List[str]:
        """Extract organization names"""
        organizations = set()
        
        for keyword in self.organization_keywords:
            pattern = f'([A-Z][a-zA-Z\\s]+){re.escape(keyword)}'
            matches = re.findall(pattern, text)
            organizations.update([m.strip() + ' ' + keyword for m in matches])
        
        return list(organizations)[:10]
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract location names"""
        locations = set()
        
        # Common location patterns
        location_keywords = ['in ', 'from ', 'to ', 'at ']
        
        for keyword in location_keywords:
            pattern = f'{keyword}([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)'
            matches = re.findall(pattern, text)
            locations.update(matches)
        
        return list(locations)[:10]
    
    def _extract_miscellaneous(self, text: str) -> List[str]:
        """Extract miscellaneous entities like dates, numbers"""
        misc = set()
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        misc.update(re.findall(date_pattern, text))
        
        # Extract years
        year_pattern = r'\b(19|20)\d{2}\b'
        misc.update(re.findall(year_pattern, text))
        
        # Extract percentages
        percent_pattern = r'\b\d+%\b'
        misc.update(re.findall(percent_pattern, text))
        
        return list(misc)[:10]

# Global instance
entity_extractor = EntityExtractor()
