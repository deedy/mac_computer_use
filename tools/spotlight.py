import Foundation
from typing import List, Dict

class SpotlightSearch:
    """Integration with macOS Spotlight search"""
    
    def search(self, query: str, attributes: List[str] = None) -> List[Dict]:
        """Search files using Spotlight"""
        # Create metadata query
        query = Foundation.NSMetadataQuery.alloc().init()
        pred = Foundation.NSPredicate.predicateWithFormat_(query)
        query.setPredicate_(pred)
        
        if attributes:
            query.setSearchAttributes_(attributes)
            
        # Start search
        Foundation.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, 
            'queryComplete:', 
            Foundation.NSMetadataQueryDidFinishGatheringNotification,
            query
        )
        
        query.startQuery()
        Foundation.NSRunLoop.currentRunLoop().runUntilDate_(
            Foundation.NSDate.dateWithTimeIntervalSinceNow_(1.0)
        )
        
        # Get results
        results = []
        for item in query.results():
            result = {
                'path': item.valueForAttribute_('kMDItemPath'),
                'name': item.valueForAttribute_('kMDItemDisplayName'),
                'type': item.valueForAttribute_('kMDItemContentType'),
                'modified': item.valueForAttribute_('kMDItemContentModificationDate')
            }
            results.append(result)
            
        return results 