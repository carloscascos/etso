"""
OBSERVATORIO ETS - Research Storage Manager
Manages research findings between ChromaDB and ETSO database
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from database import DatabaseManager, ETSODataAccess
from config import SystemConfig

logger = logging.getLogger(__name__)

@dataclass
class ResearchFinding:
    """Structure for research finding data"""
    quarter: str
    theme_type: str
    user_guidance: str
    enhanced_query: str
    research_content: str
    validation_targets: List[str]
    expected_outputs: List[str]
    research_scope: Dict[str, Any]
    confidence: float = 0.0
    status: str = 'pending'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ChromaDBManager:
    """Manages ChromaDB operations for research storage and retrieval"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.chroma_config = config.chroma.CHROMA_CONFIG
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize ChromaDB client
        self._init_chroma_client()
        
        logger.info(f"✅ ChromaDB initialized: {self.chroma_config['collection_name']}")
    
    def _init_chroma_client(self):
        """Initialize ChromaDB client based on configuration"""
        try:
            if self.chroma_config['use_server']:
                # Use ChromaDB server
                self.client = chromadb.HttpClient(
                    host=self.chroma_config['host'],
                    port=self.chroma_config['port']
                )
                logger.info(f"📡 Using ChromaDB server at {self.chroma_config['host']}:{self.chroma_config['port']}")
            else:
                # Use local persistent client
                self.client = chromadb.PersistentClient(
                    path=self.chroma_config['persist_directory'],
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"💾 Using local ChromaDB at {self.chroma_config['persist_directory']}")
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.chroma_config['collection_name']
            )
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            raise
    
    def store_research_finding(self, finding: ResearchFinding) -> str:
        """Store research finding in ChromaDB with vector embedding"""
        
        chroma_id = str(uuid.uuid4())
        
        try:
            # Prepare metadata
            metadata = {
                'quarter': finding.quarter,
                'theme_type': finding.theme_type,
                'user_guidance': finding.user_guidance[:500],  # Truncate for metadata
                'enhanced_query': finding.enhanced_query[:500],
                'validation_targets': json.dumps(finding.validation_targets),
                'expected_outputs': json.dumps(finding.expected_outputs),
                'research_scope': json.dumps(finding.research_scope),
                'confidence': finding.confidence,
                'status': finding.status,
                'timestamp': datetime.now().isoformat(),
                'content_length': len(finding.research_content)
            }
            
            # Store in ChromaDB
            self.collection.add(
                documents=[finding.research_content],
                metadatas=[metadata],
                ids=[chroma_id]
            )
            
            logger.info(f"✅ Research finding stored in ChromaDB: {chroma_id}")
            return chroma_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store in ChromaDB: {e}")
            raise
    
    def retrieve_research_finding(self, chroma_id: str) -> Optional[ResearchFinding]:
        """Retrieve research finding from ChromaDB by ID"""
        
        try:
            result = self.collection.get(
                ids=[chroma_id],
                include=['documents', 'metadatas']
            )
            
            if not result['documents']:
                logger.warning(f"⚠️  Research finding not found: {chroma_id}")
                return None
            
            document = result['documents'][0]
            metadata = result['metadatas'][0]
            
            # Reconstruct ResearchFinding
            finding = ResearchFinding(
                quarter=metadata['quarter'],
                theme_type=metadata['theme_type'],
                user_guidance=metadata['user_guidance'],
                enhanced_query=metadata['enhanced_query'],
                research_content=document,
                validation_targets=json.loads(metadata.get('validation_targets', '[]')),
                expected_outputs=json.loads(metadata.get('expected_outputs', '[]')),
                research_scope=json.loads(metadata.get('research_scope', '{}')),
                confidence=metadata.get('confidence', 0.0),
                status=metadata.get('status', 'pending')
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve from ChromaDB: {e}")
            return None
    
    def semantic_search(self, query: str, quarter: Optional[str] = None, 
                       theme_type: Optional[str] = None, n_results: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search across research findings"""
        
        try:
            # Build where clause for filtering
            where_clause = {}
            if quarter:
                where_clause['quarter'] = quarter
            if theme_type:
                where_clause['theme_type'] = theme_type
            
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0] if results['distances'] else [0] * len(results['documents'][0])
                )):
                    search_results.append({
                        'document': doc,
                        'metadata': metadata,
                        'similarity': 1 - distance,  # Convert distance to similarity
                        'rank': i + 1
                    })
            
            logger.info(f"🔍 Semantic search found {len(search_results)} results for: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []
    
    def get_research_by_quarter(self, quarter: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all research findings for a specific quarter"""
        
        try:
            results = self.collection.get(
                where={'quarter': quarter},
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            findings = []
            if results['documents']:
                for doc, metadata in zip(results['documents'], results['metadatas']):
                    findings.append({
                        'document': doc,
                        'metadata': metadata
                    })
            
            logger.info(f"📋 Retrieved {len(findings)} findings for quarter {quarter}")
            return findings
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve quarter findings: {e}")
            return []
    
    def update_finding_confidence(self, chroma_id: str, confidence: float, status: str = 'completed'):
        """Update confidence score and status for a finding"""
        
        try:
            # ChromaDB doesn't support direct metadata updates, so we need to:
            # 1. Get the current document
            # 2. Update metadata
            # 3. Re-add with same ID (overwrites)
            
            current = self.collection.get(
                ids=[chroma_id],
                include=['documents', 'metadatas']
            )
            
            if not current['documents']:
                logger.warning(f"⚠️  Cannot update - finding not found: {chroma_id}")
                return False
            
            # Update metadata
            metadata = current['metadatas'][0]
            metadata['confidence'] = confidence
            metadata['status'] = status
            metadata['updated_at'] = datetime.now().isoformat()
            
            # Re-add with updated metadata
            self.collection.upsert(
                documents=current['documents'],
                metadatas=[metadata],
                ids=[chroma_id]
            )
            
            logger.info(f"✅ Updated ChromaDB finding confidence: {chroma_id} -> {confidence:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update ChromaDB confidence: {e}")
            return False

class ResearchStorageManager:
    """Integrated storage manager for research findings"""
    
    def __init__(self, db_manager: DatabaseManager, config: SystemConfig):
        self.db_manager = db_manager
        self.etso_access = ETSODataAccess(db_manager)
        self.chroma_manager = ChromaDBManager(config)
        
        logger.info("✅ Research storage manager initialized")
    
    def store_research_finding(self, finding: ResearchFinding) -> Tuple[str, int]:
        """Store research finding in both ChromaDB and ETSO database"""
        
        logger.info(f"💾 Storing research finding: {finding.theme_type} for {finding.quarter}")
        
        try:
            # 1. Store in ChromaDB first (with vector embedding)
            chroma_id = self.chroma_manager.store_research_finding(finding)
            
            # 2. Store metadata in ETSO database
            metadata = {
                'chroma_id': chroma_id,
                'quarter': finding.quarter,
                'theme_type': finding.theme_type,
                'user_guidance': finding.user_guidance,
                'enhanced_query': finding.enhanced_query,
                'status': finding.status
            }
            
            research_id = self.etso_access.store_research_metadata(metadata)
            
            logger.info(f"✅ Research finding stored: ChromaDB={chroma_id}, ETSO DB={research_id}")
            return chroma_id, research_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store research finding: {e}")
            raise
    
    def get_research_finding(self, research_id: int) -> Optional[ResearchFinding]:
        """Get complete research finding by ETSO database ID"""
        
        try:
            # 1. Get metadata from ETSO database
            metadata = self.etso_access.get_research_metadata(research_id)
            
            if not metadata:
                logger.warning(f"⚠️  Research metadata not found: {research_id}")
                return None
            
            # 2. Get full content from ChromaDB
            finding = self.chroma_manager.retrieve_research_finding(metadata['chroma_id'])
            
            if finding:
                # Update with database metadata
                finding.confidence = metadata.get('overall_confidence', 0.0)
                finding.status = metadata.get('status', 'pending')
            
            return finding
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve research finding: {e}")
            return None
    
    def update_research_confidence(self, research_id: int, confidence: float, status: str = 'completed'):
        """Update confidence in both storage systems"""
        
        try:
            # 1. Update ETSO database
            self.etso_access.update_research_confidence(research_id, confidence, status)
            
            # 2. Get ChromaDB ID and update there too
            metadata = self.etso_access.get_research_metadata(research_id)
            if metadata:
                self.chroma_manager.update_finding_confidence(
                    metadata['chroma_id'], confidence, status
                )
            
            logger.info(f"✅ Updated research confidence: {research_id} -> {confidence:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update research confidence: {e}")
            raise
    
    def semantic_search_for_report(self, topic: str, quarter: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant research findings to include in reports"""
        
        logger.info(f"🔍 Searching for report content: {topic} in {quarter}")
        
        try:
            # Semantic search in ChromaDB
            search_results = self.chroma_manager.semantic_search(
                query=topic,
                quarter=quarter,
                n_results=limit
            )
            
            # Enrich with ETSO database validation data
            enriched_results = []
            for result in search_results:
                chroma_id = result['metadata'].get('chroma_id')
                
                # Try to find corresponding research metadata
                research_metadata = self._find_research_by_chroma_id(chroma_id)
                
                enriched_result = {
                    **result,
                    'research_metadata': research_metadata,
                    'validation_summary': self._get_validation_summary(research_metadata['id']) if research_metadata else None
                }
                
                enriched_results.append(enriched_result)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"❌ Semantic search for report failed: {e}")
            return []
    
    def _find_research_by_chroma_id(self, chroma_id: str) -> Optional[Dict[str, Any]]:
        """Find research metadata by ChromaDB ID"""
        
        try:
            query = "SELECT * FROM research_metadata WHERE chroma_id = %s"
            results = self.db_manager.execute_etso_query(query, (chroma_id,))
            
            if results:
                row = results[0]
                return {
                    'id': row[0],
                    'chroma_id': row[1],
                    'quarter': row[2],
                    'theme_type': row[3],
                    'user_guidance': row[4],
                    'enhanced_query': row[5],
                    'validation_score': row[6],
                    'overall_confidence': row[7],
                    'status': row[8]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to find research by ChromaDB ID: {e}")
            return None
    
    def _get_validation_summary(self, research_id: int) -> Optional[Dict[str, Any]]:
        """Get validation summary for research finding"""
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_claims,
                COUNT(CASE WHEN supports_claim = TRUE THEN 1 END) as supported_claims,
                AVG(confidence_score) as avg_confidence,
                MAX(validation_timestamp) as last_validation
            FROM validation_claims 
            WHERE research_metadata_id = %s
            """
            
            results = self.db_manager.execute_etso_query(query, (research_id,))
            
            if results:
                row = results[0]
                return {
                    'total_claims': row[0],
                    'supported_claims': row[1],
                    'avg_confidence': float(row[2]) if row[2] else 0.0,
                    'last_validation': row[3],
                    'support_rate': (row[1] / row[0]) if row[0] > 0 else 0.0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get validation summary: {e}")
            return None
    
    def get_quarterly_research_summary(self, quarter: str) -> Dict[str, Any]:
        """Get comprehensive summary of research for a quarter"""
        
        try:
            # Get summary from ETSO database
            db_summary = self.etso_access.get_quarterly_summary(quarter)
            
            # Get research findings from ChromaDB
            chroma_findings = self.chroma_manager.get_research_by_quarter(quarter)
            
            # Combine into comprehensive summary
            return {
                'quarter': quarter,
                'database_summary': db_summary,
                'total_findings_chroma': len(chroma_findings),
                'findings_by_theme': self._summarize_by_theme(chroma_findings),
                'confidence_distribution': self._analyze_confidence_distribution(chroma_findings),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get quarterly summary: {e}")
            return {}
    
    def _summarize_by_theme(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize findings by theme type"""
        
        theme_counts = {}
        for finding in findings:
            theme = finding['metadata'].get('theme_type', 'unknown')
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        return theme_counts
    
    def _analyze_confidence_distribution(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze confidence score distribution"""
        
        confidences = [
            finding['metadata'].get('confidence', 0.0) 
            for finding in findings 
            if finding['metadata'].get('confidence') is not None
        ]
        
        if not confidences:
            return {'count': 0, 'avg': 0.0, 'high': 0, 'medium': 0, 'low': 0}
        
        return {
            'count': len(confidences),
            'avg': sum(confidences) / len(confidences),
            'high': len([c for c in confidences if c >= 0.8]),
            'medium': len([c for c in confidences if 0.5 <= c < 0.8]),
            'low': len([c for c in confidences if c < 0.5])
        }

# Convenience function to create storage manager
def create_storage_manager(db_manager: DatabaseManager = None, config: SystemConfig = None) -> ResearchStorageManager:
    """Create research storage manager with dependencies"""
    
    if config is None:
        from config import config as default_config
        config = default_config
    
    if db_manager is None:
        from database import create_database_manager
        db_manager = create_database_manager(config)
    
    return ResearchStorageManager(db_manager, config)