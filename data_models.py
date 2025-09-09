# data_models.py - Python Data Models for Bihar ul Anwar Final Schema
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import json

class ContentType(Enum):
    HADITH = "hadith"
    VERSE = "verse"
    COMMENTARY = "commentary"
    CHAPTER_HEADER = "chapter_header"
    NAVIGATION = "navigation"

class EmbeddingModel(Enum):
    GEMINI_TEXT_EMBEDDING_004 = "gemini-text-embedding-004"
    LLAMA_EMBEDDING = "llama-embedding"
    QWEN_EMBEDDING = "qwen-embedding"

class LanguageCode(Enum):
    ARABIC = "ar"
    ENGLISH = "en"
    URDU = "ur"
    PERSIAN = "fa"

@dataclass
class BaseModel:
    """Base model with audit fields"""
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    modified_by: str = "system"
    modified_at: datetime = field(default_factory=datetime.now)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

@dataclass
class Topic(BaseModel):
    """Topic classification for hadiths and chapters"""
    t_id: Optional[int] = None
    topic_name_en: str = ""
    topic_name_ar: str = ""

    def __post_init__(self):
        if not self.topic_name_en and not self.topic_name_ar:
            raise ValueError("At least one of topic_name_en or topic_name_ar is required")

@dataclass
class Volume(BaseModel):
    """Bihar ul Anwar Volume"""
    v_id: Optional[int] = None
    v_no: int = 0
    v_name_en: str = ""
    v_name_ar: str = ""
    v_total_chapters: int = 0
    v_module: str = ""  # Theme/topic of volume
    v_pdf_path: str = ""
    v_total_pages: int = 0
    v_file_size_mb: float = 0.0
    v_processing_status: str = "pending"  # pending, processing, completed, error
    v_quality_score: float = 0.0

    def __post_init__(self):
        if not (1 <= self.v_no <= 110):
            raise ValueError(f"Volume number must be between 1 and 110, got {self.v_no}")

    @property
    def is_processed(self) -> bool:
        return self.v_processing_status == "completed"
    
    @property
    def display_name(self) -> str:
        return self.v_name_en or self.v_name_ar or f"Volume {self.v_no}"

@dataclass
class Chapter(BaseModel):
    """Chapter within a volume"""
    c_id: Optional[int] = None
    c_no: int = 0
    c_name_en: str = ""
    c_name_ar: str = ""
    c_total_hadith: int = 0
    c_total_verses: int = 0
    c_description_en: str = ""
    c_description_ar: str = ""
    c_topic_keywords: List[str] = field(default_factory=list)
    c_v_id: int = 0  # Foreign key to volumes

    @property
    def display_name(self) -> str:
        return self.c_name_en or self.c_name_ar or f"Chapter {self.c_no}"
    
    @property
    def has_content(self) -> bool:
        return self.c_total_hadith > 0 or self.c_total_verses > 0

@dataclass
class Hadith(BaseModel):
    """Complete hadith with all metadata"""
    h_id: Optional[int] = None
    h_no: int = 0
    h_hadith_ref: str = ""  # BH_V{v}_C{c}_H{h}
    h_narrator_chain_length: int = 0
    h_narrator_final_ar: str = ""
    h_narrator_final_en: str = ""
    h_source_book_ar: str = ""
    h_source_book_en: str = ""
    h_isnad_ar: str = ""  # Chain of narration
    h_isnad_en: str = ""  # Chain of narration
    h_matn_ar: str = ""  # Main hadith text (required)
    h_matn_en: str = ""  # Main hadith text (required)
    h_explanation_ar: str = ""  # Optional explanation
    h_explanation_en: str = ""  # Optional explanation
    h_normalized_text: str = ""  # For search optimization
    h_text_quality_score: float = 0.0
    h_topics: List[str] = field(default_factory=list)
    h_c_id: int = 0  # Foreign key to chapters
    h_raw_json: Dict[str, Any] = field(default_factory=dict)
    h_extraction_confidence: float = 0.0
    h_is_verified: bool = False
    h_verified_by: Optional[str] = None
    h_verified_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.h_matn_ar:
            raise ValueError("Arabic hadith text (h_matn_ar) is required")
        if not self.h_matn_en:
            raise ValueError("English hadith text (h_matn_en) is required")
        
        # Generate normalized text if not provided
        if not self.h_normalized_text:
            self.h_normalized_text = self._generate_normalized_text()
    
    def _generate_normalized_text(self) -> str:
        """Generate normalized text for search"""
        import re
        # Combine English and Arabic text
        combined = f"{self.h_matn_en} {self.h_matn_ar} {self.h_isnad_en}"
        # Basic normalization
        normalized = re.sub(r'\s+', ' ', combined.strip())
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        return normalized.lower()
    
    @property
    def is_bilingual(self) -> bool:
        """Check if hadith has both Arabic and English content"""
        return bool(self.h_matn_ar and self.h_matn_en)
    
    @property
    def has_isnad(self) -> bool:
        """Check if hadith has chain of narration"""
        return bool(self.h_isnad_ar or self.h_isnad_en)
    
    @property
    def full_citation(self) -> str:
        """Get formatted citation"""
        if self.h_hadith_ref:
            # Parse BH_V1_C2_H3 format
            parts = self.h_hadith_ref.replace('BH_V', '').replace('_C', ', Chapter ').replace('_H', ', Hadith ')
            return f"Bihar ul Anwar, Volume {parts}"
        return f"Bihar ul Anwar, Volume ?, Chapter ?, Hadith {self.h_no}"
    
    def get_text_by_language(self, language: LanguageCode) -> Optional[str]:
        """Get hadith text in specific language"""
        if language == LanguageCode.ARABIC:
            return self.h_matn_ar
        elif language == LanguageCode.ENGLISH:
            return self.h_matn_en
        return None
    
    def get_isnad_by_language(self, language: LanguageCode) -> Optional[str]:
        """Get isnad in specific language"""
        if language == LanguageCode.ARABIC:
            return self.h_isnad_ar
        elif language == LanguageCode.ENGLISH:
            return self.h_isnad_en
        return None

@dataclass
class Verse(BaseModel):
    """Quranic verse referenced in a chapter"""
    vr_id: Optional[int] = None
    vr_no: int = 0
    vr_surah_no: int = 0
    vr_surah_name_ar: str = ""
    vr_surah_name_en: str = ""
    vr_ayat_start: int = 0
    vr_ayat_end: Optional[int] = None
    vr_ar: str = ""  # Arabic verse text
    vr_en: str = ""  # English verse text
    vr_c_id: int = 0  # Foreign key to chapters

    def __post_init__(self):
        if not (1 <= self.vr_surah_no <= 114):
            raise ValueError(f"Surah number must be between 1 and 114, got {self.vr_surah_no}")
        if self.vr_ayat_end and self.vr_ayat_end < self.vr_ayat_start:
            raise ValueError("End ayah must be >= start ayah")
        if not self.vr_ar:
            raise ValueError("Arabic verse text is required")
    
    @property
    def ayah_range(self) -> str:
        """Get formatted ayah range"""
        if self.vr_ayat_end and self.vr_ayat_end != self.vr_ayat_start:
            return f"{self.vr_ayat_start}-{self.vr_ayat_end}"
        return str(self.vr_ayat_start)
    
    @property
    def citation(self) -> str:
        """Get Quranic citation"""
        surah_name = self.vr_surah_name_en or f"Surah {self.vr_surah_no}"
        return f"{surah_name} {self.ayah_range}"

@dataclass
class Edition(BaseModel):
    """Publication edition for page references"""
    e_id: Optional[int] = None
    e_name: str = ""
    e_publisher: str = ""
    e_year_published: int = 0
    e_language: LanguageCode = LanguageCode.ARABIC
    e_is_canonical: bool = False
    e_pdf_available: bool = False
    e_total_volumes: int = 110
    e_notes: str = ""

@dataclass
class HadithPage(BaseModel):
    """Page reference for hadith in specific edition"""
    hp_id: Optional[int] = None
    hp_h_id: int = 0  # Foreign key to hadiths
    hp_e_id: int = 0  # Foreign key to editions
    hp_page_start: int = 0
    hp_page_end: Optional[int] = None
    hp_pdf_offset_start: Optional[int] = None
    hp_pdf_offset_end: Optional[int] = None

    def __post_init__(self):
        if self.hp_page_end and self.hp_page_end < self.hp_page_start:
            raise ValueError("End page must be >= start page")
    
    @property
    def page_range(self) -> str:
        """Get formatted page range"""
        if self.hp_page_end and self.hp_page_end != self.hp_page_start:
            return f"pp. {self.hp_page_start}-{self.hp_page_end}"
        return f"p. {self.hp_page_start}"

@dataclass
class SearchDocument(BaseModel):
    """Document for RAG retrieval"""
    sd_id: Optional[int] = None
    sd_hadith_ref: str = ""  # References hadiths.h_hadith_ref
    sd_content_type: ContentType = ContentType.HADITH
    sd_language: LanguageCode = LanguageCode.ENGLISH
    sd_content: str = ""
    sd_normalized_content: str = ""
    sd_chunk_metadata: Dict[str, Any] = field(default_factory=dict)
    sd_chunk_size: int = 0

    def __post_init__(self):
        if not self.sd_content:
            raise ValueError("Content is required")
        
        # Calculate chunk size
        self.sd_chunk_size = len(self.sd_content)
        
        # Generate normalized content if not provided
        if not self.sd_normalized_content:
            self.sd_normalized_content = self._normalize_content()
    
    def _normalize_content(self) -> str:
        """Normalize content for search"""
        import re
        normalized = re.sub(r'\s+', ' ', self.sd_content.strip())
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        return normalized.lower()

@dataclass
class Embedding(BaseModel):
    """Vector embedding for semantic search"""
    emb_id: Optional[int] = None
    emb_sd_id: int = 0  # Foreign key to search_documents
    emb_model: EmbeddingModel = EmbeddingModel.GEMINI_TEXT_EMBEDDING_004
    emb_version: str = "v1"
    emb_embedding: List[float] = field(default_factory=list)
    emb_is_active: bool = True

    def __post_init__(self):
        if not self.emb_embedding:
            raise ValueError("Embedding vector is required")
        if len(self.emb_embedding) != 768:  # Assuming 768-dimensional embeddings
            print(f"Warning: Expected 768-dimensional embedding, got {len(self.emb_embedding)}")

# Utility functions for data manipulation
def generate_hadith_ref(volume_no: int, chapter_no: int, hadith_no: int) -> str:
    """Generate canonical hadith reference"""
    return f"BH_V{volume_no}_C{chapter_no}_H{hadith_no}"

def parse_hadith_ref(hadith_ref: str) -> Dict[str, int]:
    """Parse hadith reference into components"""
    import re
    match = re.match(r'BH_V(\d+)_C(\d+)_H(\d+)', hadith_ref)
    if not match:
        raise ValueError(f"Invalid hadith reference format: {hadith_ref}")
    
    return {
        'volume': int(match.group(1)),
        'chapter': int(match.group(2)),
        'hadith': int(match.group(3))
    }

def validate_hadith_data(hadith: Hadith) -> Dict[str, bool]:
    """Validate hadith data structure"""
    return {
        'has_valid_ref': bool(hadith.h_hadith_ref and 'BH_V' in hadith.h_hadith_ref),
        'has_arabic_text': bool(hadith.h_matn_ar),
        'has_english_text': bool(hadith.h_matn_en),
        'has_isnad': bool(hadith.h_isnad_ar or hadith.h_isnad_en),
        'has_topics': len(hadith.h_topics) > 0,
        'is_verified': hadith.h_is_verified,
        'good_quality': hadith.h_text_quality_score > 0.7,
        'is_bilingual': hadith.is_bilingual
    }

# Example data creation functions
def create_sample_volume() -> Volume:
    """Create sample volume for testing"""
    return Volume(
        v_no=1,
        v_name_en="The Book of Intellect and Ignorance",
        v_name_ar="كتاب العقل والجهل",
        v_module="Theology",
        v_processing_status="pending"
    )

def create_sample_hadith() -> Hadith:
    """Create sample hadith for testing"""
    return Hadith(
        h_no=1,
        h_hadith_ref="BH_V1_C1_H1",
        h_narrator_final_en="Imam Ali (AS)",
        h_narrator_final_ar="الإمام علي عليه السلام",
        h_source_book_en="Al-Kafi",
        h_source_book_ar="الكافي",
        h_isnad_en="Muhammad ibn Yahya narrated from Ahmad ibn Muhammad",
        h_isnad_ar="حدثنا محمد بن يحيى عن أحمد بن محمد",
        h_matn_en="Intellect is a light in the heart by which one distinguishes between truth and falsehood",
        h_matn_ar="العقل نور في القلب يفرق به بين الحق والباطل",
        h_topics=["intellect", "knowledge", "theology"],
        h_c_id=1,
        h_text_quality_score=0.95,
        h_extraction_confidence=0.90
    )

# Testing and validation
if __name__ == "__main__":
    print("🧪 Testing Bihar ul Anwar Data Models")
    print("=" * 50)
    
    # Test volume creation
    volume = create_sample_volume()
    print(f"✅ Volume created: {volume.display_name}")
    print(f"   Status: {volume.v_processing_status}")
    print(f"   Processed: {volume.is_processed}")
    
    # Test hadith creation
    hadith = create_sample_hadith()
    print(f"\n✅ Hadith created: {hadith.h_hadith_ref}")
    print(f"   Citation: {hadith.full_citation}")
    print(f"   Bilingual: {hadith.is_bilingual}")
    print(f"   Has Isnad: {hadith.has_isnad}")
    
    # Test hadith validation
    validation = validate_hadith_data(hadith)
    print(f"\n📊 Hadith validation:")
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    # Test hadith reference parsing
    parsed = parse_hadith_ref(hadith.h_hadith_ref)
    print(f"\n🔍 Parsed reference:")
    print(f"   Volume: {parsed['volume']}")
    print(f"   Chapter: {parsed['chapter']}")
    print(f"   Hadith: {parsed['hadith']}")
    
    print(f"\n✅ All data models working correctly!")
    print(f"📋 Ready for database integration and intelligent parsing!")