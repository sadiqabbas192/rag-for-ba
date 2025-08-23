-- ===================================================================================================================
-- ******************************************* BIHAR-UL-ANWAR DB *****************************************************
-- ===================================================================================================================

-- ************************************************ CORE TABLES *******************************************************
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Enums for data integrity
CREATE TYPE content_type AS ENUM ('hadith', 'verse', 'commentary', 'chapter_header', 'navigation');
CREATE TYPE embedding_model AS ENUM ('gemini-text-embedding-004', 'llama-embedding', 'qwen-embedding');
CREATE TYPE language_code AS ENUM ('ar', 'en', 'ur', 'fa');

-- table topics
CREATE TABLE topics (
    t_id SERIAL PRIMARY KEY,
    topic_name_en VARCHAR(300) UNIQUE,
    topic_name_ar VARCHAR(300),
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100) 
);

-- table volumes
CREATE TABLE volumes (
    v_id SERIAL PRIMARY KEY,
    v_no INTEGER UNIQUE NOT NULL CHECK (v_no BETWEEN 1 AND 110),
    v_name_en VARCHAR(500),
    v_name_ar VARCHAR(500),
    v_total_chapters INTEGER DEFAULT 0,
    v_module VARCHAR(100), -- Theme/topic of volume
    v_pdf_path VARCHAR(1000),
    v_total_pages INTEGER,
    v_file_size_mb DECIMAL(10,2),
    v_processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, error
    v_quality_score DECIMAL(3,2) DEFAULT 0.0,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100)
);

-- table chapters
CREATE TABLE chapters (
    c_id SERIAL PRIMARY KEY,
    c_no INTEGER NOT NULL,
    c_name_en VARCHAR(1000),
    c_name_ar VARCHAR(1000),
    c_total_hadith INTEGER DEFAULT 0,
    c_total_verses INTEGER DEFAULT 0,
    c_description_en TEXT,
    c_description_ar TEXT,
    c_topic_keywords TEXT[], -- Array of keywords for this chapter
    c_v_id INTEGER NOT NULL,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT chapters_v_id_fk FOREIGN KEY (c_v_id) REFERENCES volumes(v_id) ON DELETE CASCADE,
    -- unique constraints
    UNIQUE(c_v_id, c_no)
);

-- table hadiths
CREATE TABLE hadiths (
    h_id SERIAL PRIMARY KEY,
    h_no INTEGER NOT NULL,
    h_hadith_ref VARCHAR(50) UNIQUE NOT NULL, -- BH_V{v}_C{c}_H{h}
    h_narrator_chain_length INTEGER DEFAULT 0,
    h_narrator_final_ar VARCHAR(300), -- Final narrator in chain in ar
    h_narrator_final_en VARCHAR(300), -- Final narrator in chain in en
    h_source_book_ar VARCHAR(500), -- e.g., "Al-Kafi"
    h_source_book_en VARCHAR(500), -- e.g., "Al-Kafi"
    h_isnad_ar TEXT, -- Chain of narration
    h_isnad_en TEXT, -- Chain of narration
    h_matn_ar TEXT NOT NULL, -- Main hadith text
    h_matn_en TEXT NOT NULL, -- Main hadith text
    h_explanation_ar TEXT, -- Optional explanation in ar
    h_explanation_en TEXT, -- Optional explanation in en
    h_normalized_text TEXT, -- For search optimization (cleaned, stemmed)
    h_text_quality_score DECIMAL(3,2) DEFAULT 0.0,
    h_topics TEXT[], -- Array of topic keywords
    h_c_id INTEGER NOT NULL,
    h_raw_json JSONB, -- Sidecar for original parsed data
    h_extraction_confidence DECIMAL(3,2) DEFAULT 0.0,
    h_is_verified BOOLEAN DEFAULT FALSE,
    h_verified_by VARCHAR(100),
    h_verified_at TIMESTAMP WITH TIME ZONE,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT hadiths_c_id_fk FOREIGN KEY (h_c_id) REFERENCES chapters(c_id) ON DELETE CASCADE,
    -- unique constraints
    UNIQUE(h_c_id, h_no)
);

-- table verses
CREATE TABLE verses (
    vr_id SERIAL PRIMARY KEY,
    vr_no INTEGER,
    vr_surah_no INTEGER NOT NULL CHECK (vr_surah_no BETWEEN 1 AND 114),
    vr_surah_name_ar VARCHAR(100),
    vr_surah_name_en VARCHAR(100),
    vr_ayat_start INTEGER NOT NULL,
    vr_ayat_end INTEGER,
    vr_ar TEXT NOT NULL,
    vr_en TEXT,
    vr_c_id INTEGER NOT NULL,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT verses_c_id_fk FOREIGN KEY (vr_c_id) REFERENCES chapters(c_id) ON DELETE CASCADE,
    -- check constraints
    CHECK (vr_ayat_end IS NULL OR vr_ayat_end >= vr_ayat_start)
);

-- table editions
CREATE TABLE editions (
    e_id SERIAL PRIMARY KEY,
    e_name VARCHAR(300) UNIQUE,
    e_publisher VARCHAR(300),
    e_year_published INTEGER,
    e_language language_code DEFAULT 'ar',
    e_is_canonical BOOLEAN DEFAULT FALSE,
    e_pdf_available BOOLEAN DEFAULT FALSE,
    e_total_volumes INTEGER DEFAULT 110,
    e_notes TEXT,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100)
);

-- table hadith_pages
CREATE TABLE hadith_pages (
    hp_id SERIAL PRIMARY KEY,
    hp_h_id INTEGER NOT NULL,
    hp_e_id INTEGER NOT NULL,
    hp_page_start INTEGER NOT NULL,
    hp_page_end INTEGER,
    hp_pdf_offset_start INTEGER, -- For direct PDF navigation
    hp_pdf_offset_end INTEGER,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT hadith_pages_h_id_fk FOREIGN KEY (hp_h_id) REFERENCES hadiths(h_id) ON DELETE CASCADE,
    CONSTRAINT hadith_pages_e_id_fk FOREIGN KEY (hp_e_id) REFERENCES editions(e_id) ON DELETE CASCADE,
    -- unique constraints
    UNIQUE(hp_h_id, hp_e_id),
    -- check constraints
    CHECK (hp_page_end IS NULL OR hp_page_end >= hp_page_start)
);

-- ---------- RAG Retrieval Layer ----------
-- table search_documents
CREATE TABLE search_documents (
    sd_id SERIAL PRIMARY KEY,
    sd_hadith_ref VARCHAR(50) NOT NULL, -- References hadiths.h_hadith_ref
    sd_content_type content_type NOT NULL,
    sd_language language_code NOT NULL,
    sd_content TEXT NOT NULL,
    sd_normalized_content TEXT, -- For BM25 and keyword search
    sd_chunk_metadata JSONB NOT NULL, -- Denormalized coords + metadata
    sd_chunk_size INTEGER,
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT search_docs_hadith_ref_fk FOREIGN KEY (sd_hadith_ref) REFERENCES hadiths(h_hadith_ref) ON DELETE CASCADE
);

-- ---------- Vector Embeddings (versioned for model migrations) ----------
-- table embeddings
CREATE TABLE embeddings (
    emb_id SERIAL PRIMARY KEY,
    emb_sd_id INTEGER NOT NULL,
    emb_model embedding_model NOT NULL,
    emb_version VARCHAR(50) DEFAULT 'v1',
    emb_embedding VECTOR(768), -- Adjust dimension as needed
    emb_is_active BOOLEAN DEFAULT TRUE, -- For A/B testing during model migrations
    -- audit and logs
    created_by VARCHAR(100) NOT NULL DEFAULT current_user,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    modified_by VARCHAR(100) NOT NULL DEFAULT current_user,
    modified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT current_timestamp,
    -- soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(100),
    -- foreign key constraints
    CONSTRAINT embeddings_sd_id_fk FOREIGN KEY (emb_sd_id) REFERENCES search_documents(sd_id) ON DELETE CASCADE,
    -- unique constraints
    UNIQUE(emb_sd_id, emb_model, emb_version)
);

-- *************************************************** INDEXES *******************************************************

-- Performance Indexes
CREATE INDEX idx_volumes_v_no ON volumes(v_no) WHERE is_deleted = false;
CREATE INDEX idx_volumes_status ON volumes(v_processing_status) WHERE is_deleted = false;

CREATE INDEX idx_chapters_v_id_c_no ON chapters(c_v_id, c_no) WHERE is_deleted = false;
CREATE INDEX idx_chapters_keywords ON chapters USING GIN(c_topic_keywords) WHERE is_deleted = false;

CREATE INDEX idx_hadiths_hadith_ref ON hadiths(h_hadith_ref) WHERE is_deleted = false;
CREATE INDEX idx_hadiths_c_id_h_no ON hadiths(h_c_id, h_no) WHERE is_deleted = false;
CREATE INDEX idx_hadiths_verified ON hadiths(h_is_verified) WHERE is_deleted = false;
CREATE GIN INDEX idx_hadiths_topics ON hadiths USING GIN(h_topics) WHERE is_deleted = false;
CREATE GIN INDEX idx_hadiths_raw_json ON hadiths USING GIN(h_raw_json) WHERE is_deleted = false;

CREATE INDEX idx_verses_c_id ON verses(vr_c_id) WHERE is_deleted = false;
CREATE INDEX idx_verses_surah ON verses(vr_surah_no) WHERE is_deleted = false;

CREATE INDEX idx_search_docs_hadith_ref ON search_documents(sd_hadith_ref) WHERE is_deleted = false;
CREATE INDEX idx_search_docs_type_lang ON search_documents(sd_content_type, sd_language) WHERE is_deleted = false;
CREATE INDEX idx_search_docs_metadata ON search_documents USING GIN(sd_chunk_metadata) WHERE is_deleted = false;

CREATE INDEX idx_embeddings_model_version ON embeddings(emb_model, emb_version, emb_is_active) WHERE is_deleted = false;

-- Text search indexes
CREATE INDEX idx_hadiths_normalized_gin ON hadiths USING GIN(to_tsvector('english', h_normalized_text)) WHERE is_deleted = false;
CREATE INDEX idx_search_docs_normalized_gin ON search_documents USING GIN(to_tsvector('english', sd_normalized_content)) WHERE is_deleted = false;


-- ****************************************** TRIGGERS AND ITS FUNCTIONS *******************************************************
-- Utility functions
CREATE OR REPLACE FUNCTION generate_hadith_ref(vol_no INTEGER, chap_no INTEGER, hadith_no INTEGER)
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN CONCAT('BH_V', vol_no, '_C', chap_no, '_H', hadith_no);
END;
$$ LANGUAGE plpgsql;

-- Update counts function
CREATE OR REPLACE FUNCTION update_chapter_hadith_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update hadith count in chapters
    UPDATE chapters 
    SET c_total_hadith = (
        SELECT COUNT(*) 
        FROM hadiths 
        WHERE h_c_id = chapters.c_id AND is_deleted = false
    )
    WHERE is_deleted = false;
    
    -- Update chapter count in volumes
    UPDATE volumes 
    SET v_total_chapters = (
        SELECT COUNT(*) 
        FROM chapters 
        WHERE c_v_id = volumes.v_id AND is_deleted = false
    )
    WHERE is_deleted = false;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_hadith_counts
    AFTER INSERT OR UPDATE OR DELETE ON hadiths
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_chapter_hadith_counts();


-- ******************************************* VIEWS *******************************************************
-- Useful views
CREATE VIEW hadith_complete AS
SELECT 
    h.h_hadith_ref,
    h.h_no,
    v.v_no as volume,
    c.c_no as chapter,
    c.c_name_en as chapter_name_en,
    c.c_name_ar as chapter_name_ar,
    h.h_source_book_en,
    h.h_source_book_ar,
    h.h_topics,
    h.h_is_verified,
    h.h_isnad_ar,
    h.h_matn_ar,
    h.h_explanation_ar,
    h.h_isnad_en,
    h.h_matn_en,
    h.h_explanation_en,
    hp.hp_page_start,
    hp.hp_page_end,
    CONCAT('Bihar ul Anwar, Volume ', v.v_no, ', Chapter ', c.c_no, ', Hadith ', h.h_no) as full_citation
FROM hadiths h
JOIN chapters c ON h.h_c_id = c.c_id
JOIN volumes v ON c.c_v_id = v.v_id
LEFT JOIN hadith_pages hp ON h.h_id = hp.hp_h_id AND hp.hp_e_id = (SELECT e_id FROM editions WHERE e_is_canonical = TRUE LIMIT 1)
WHERE h.is_deleted = false AND c.is_deleted = false AND v.is_deleted = false;


-- CREATE TABLE hadith_topics (
--     ht_id SERIAL PRIMARY KEY,
--     h_id INTEGER REFERENCES hadiths(h_id) ON DELETE CASCADE,
--     t_id INTEGER REFERENCES topics(t_id),
--     confidence DECIMAL(3,2) DEFAULT 1.0, -- For ML-assigned topics (0.0-1.0)
--     is_manual BOOLEAN DEFAULT TRUE, -- TRUE=human assigned, FALSE=ML assigned
--     assigned_by VARCHAR(100),
--     assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE(h_id, t_id)
-- );

-- -- Drop existing tables if they exist (careful in production!)
-- DROP TABLE IF EXISTS embeddings CASCADE;
-- DROP TABLE IF EXISTS search_documents CASCADE;
-- DROP TABLE IF EXISTS hadith_topics CASCADE;
-- DROP TABLE IF EXISTS topics CASCADE;
-- DROP TABLE IF EXISTS hadith_pages CASCADE;
-- DROP TABLE IF EXISTS editions CASCADE;
-- DROP TABLE IF EXISTS hadith_sources CASCADE;
-- DROP TABLE IF EXISTS sources CASCADE;
-- DROP TABLE IF EXISTS verses CASCADE;
-- DROP TABLE IF EXISTS hadith_texts CASCADE;
-- DROP TABLE IF EXISTS hadiths CASCADE;
-- DROP TABLE IF EXISTS chapters CASCADE;
-- DROP TABLE IF EXISTS volumes CASCADE;
