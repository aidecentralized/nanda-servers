import os
import json
import shutil
import sqlite3
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

class PaperStore:
    """
    Class to manage storing and retrieving papers from a central repository.
    Includes metadata tracking and search functionality.
    """
    def __init__(self, store_dir: str):
        """Initialize the paper store with the specified directory"""
        self.store_dir = store_dir
        self.db_path = os.path.join(store_dir, "papers.db")

        # Create directory if it doesn't exist
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
            logger.debug(f"Created paper store directory: {store_dir}")

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database for paper metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create papers table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            abstract TEXT,
            categories TEXT,
            published_date TEXT,
            filename TEXT NOT NULL,
            download_date TEXT NOT NULL,
            citation_count INTEGER DEFAULT 0,
            fulltext_extracted BOOLEAN DEFAULT 0,
            fulltext TEXT,
            local_path TEXT NOT NULL,
            tags TEXT,
            notes TEXT
        )
        ''')

        # Create search index
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            id, title, authors, abstract, categories, fulltext,
            content=papers, content_rowid=rowid
        )
        ''')

        # Create trigger to update FTS index when papers are added
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
            INSERT INTO papers_fts(rowid, id, title, authors, abstract, categories, fulltext)
            VALUES (new.rowid, new.id, new.title, new.authors, new.abstract, new.categories, new.fulltext);
        END
        ''')

        # Create trigger to update FTS index when papers are updated
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
            INSERT INTO papers_fts(papers_fts, rowid, id, title, authors, abstract, categories, fulltext)
            VALUES ('delete', old.rowid, old.id, old.title, old.authors, old.abstract, old.categories, old.fulltext);
            INSERT INTO papers_fts(rowid, id, title, authors, abstract, categories, fulltext)
            VALUES (new.rowid, new.id, new.title, new.authors, new.abstract, new.categories, new.fulltext);
        END
        ''')

        # Create trigger to update FTS index when papers are deleted
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
            INSERT INTO papers_fts(papers_fts, rowid, id, title, authors, abstract, categories, fulltext)
            VALUES ('delete', old.rowid, old.id, old.title, old.authors, old.abstract, old.categories, old.fulltext);
        END
        ''')

        conn.commit()
        conn.close()
        logger.debug("Database initialized")

    def add_paper(self, paper_data: Dict[str, Any], source_path: str) -> bool:
        """
        Add a paper to the store

        Args:
            paper_data: Dictionary containing paper metadata
            source_path: Path to the paper file to be copied

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract paper ID and create a safe filename
            paper_id = paper_data.get('id', '').split('/')[-1]
            if not paper_id:
                logger.error("Paper ID is missing")
                return False

            # Copy the file to the store
            filename = os.path.basename(source_path)
            target_path = os.path.join(self.store_dir, filename)

            # Check if file already exists
            if os.path.exists(target_path):
                logger.info(f"Paper {paper_id} already exists in store")
                return True

            # Copy the file
            shutil.copy2(source_path, target_path)

            # Format authors list
            authors = paper_data.get('authors', [])
            if isinstance(authors, list):
                authors_str = json.dumps(authors)
            else:
                authors_str = json.dumps([authors])

            # Format categories
            categories = paper_data.get('categories', '')
            if isinstance(categories, list):
                categories_str = ','.join(categories)
            else:
                categories_str = str(categories)

            # Add to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO papers (
                id, title, authors, abstract, categories, published_date,
                filename, download_date, local_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                paper_id,
                paper_data.get('title', ''),
                authors_str,
                paper_data.get('summary', ''),
                categories_str,
                paper_data.get('published', ''),
                filename,
                datetime.now().isoformat(),
                target_path
            ))

            conn.commit()
            conn.close()

            logger.info(f"Added paper {paper_id} to store")
            return True

        except Exception as e:
            logger.error(f"Error adding paper to store: {e}")
            return False

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a paper's metadata by ID

        Args:
            paper_id: The arXiv ID of the paper

        Returns:
            Dict with paper metadata or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            result = cursor.fetchone()

            if not result:
                return None

            # Convert row to dict
            paper_data = dict(result)

            # Parse JSON fields
            if paper_data.get('authors'):
                paper_data['authors'] = json.loads(paper_data['authors'])

            if paper_data.get('tags'):
                paper_data['tags'] = paper_data['tags'].split(',')

            conn.close()
            return paper_data

        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {e}")
            return None

    def search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers using full-text search

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching paper metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Search using FTS5
            cursor.execute("""
            SELECT papers.* FROM papers
            JOIN papers_fts ON papers.rowid = papers_fts.rowid
            WHERE papers_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """, (query, limit))

            results = cursor.fetchall()
            papers = []

            for row in results:
                paper_data = dict(row)

                # Parse JSON fields
                if paper_data.get('authors'):
                    paper_data['authors'] = json.loads(paper_data['authors'])

                if paper_data.get('tags'):
                    paper_data['tags'] = paper_data['tags'].split(',')

                papers.append(paper_data)

            conn.close()
            return papers

        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []

    def get_all_papers(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all papers from the store with pagination

        Args:
            limit: Maximum number of papers to return
            offset: Starting point for pagination

        Returns:
            List of paper metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
            SELECT * FROM papers
            ORDER BY download_date DESC
            LIMIT ? OFFSET ?
            """, (limit, offset))

            results = cursor.fetchall()
            papers = []

            for row in results:
                paper_data = dict(row)

                # Parse JSON fields
                if paper_data.get('authors'):
                    paper_data['authors'] = json.loads(paper_data['authors'])

                if paper_data.get('tags'):
                    paper_data['tags'] = paper_data['tags'].split(',')

                papers.append(paper_data)

            conn.close()
            return papers

        except Exception as e:
            logger.error(f"Error retrieving all papers: {e}")
            return []

    def add_notes(self, paper_id: str, notes: str) -> bool:
        """
        Add or update notes for a paper

        Args:
            paper_id: The arXiv ID of the paper
            notes: Notes text

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE papers
            SET notes = ?
            WHERE id = ?
            """, (notes, paper_id))

            conn.commit()
            conn.close()

            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error adding notes to paper {paper_id}: {e}")
            return False

    def add_tags(self, paper_id: str, tags: List[str]) -> bool:
        """
        Add tags to a paper

        Args:
            paper_id: The arXiv ID of the paper
            tags: List of tags to add

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get existing tags
            paper = self.get_paper(paper_id)
            if not paper:
                return False

            existing_tags = paper.get('tags', [])
            if not existing_tags:
                existing_tags = []

            # Combine tags and remove duplicates
            all_tags = list(set(existing_tags + tags))
            tags_str = ','.join(all_tags)

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE papers
            SET tags = ?
            WHERE id = ?
            """, (tags_str, paper_id))

            conn.commit()
            conn.close()

            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error adding tags to paper {paper_id}: {e}")
            return False

    def find_similar_papers(self, paper_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find papers similar to the specified paper

        Args:
            paper_id: The arXiv ID of the paper
            limit: Maximum number of results to return

        Returns:
            List of similar papers
        """
        paper = self.get_paper(paper_id)
        if not paper:
            return []

        # Create search query from title and abstract
        search_terms = f"{paper['title']} {paper['abstract']}"

        # Get similar papers but exclude the input paper
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
            SELECT papers.* FROM papers
            JOIN papers_fts ON papers.rowid = papers_fts.rowid
            WHERE papers_fts MATCH ? AND papers.id != ?
            ORDER BY rank
            LIMIT ?
            """, (search_terms, paper_id, limit))

            results = cursor.fetchall()
            papers = []

            for row in results:
                paper_data = dict(row)

                # Parse JSON fields
                if paper_data.get('authors'):
                    paper_data['authors'] = json.loads(paper_data['authors'])

                if paper_data.get('tags'):
                    paper_data['tags'] = paper_data['tags'].split(',')

                papers.append(paper_data)

            conn.close()
            return papers

        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []

    def import_from_directory(self, source_dir: str, metadata_file: Optional[str] = None) -> Tuple[int, int]:
        """
        Import papers from another directory

        Args:
            source_dir: Directory containing PDF papers
            metadata_file: Optional path to JSON file with metadata

        Returns:
            Tuple of (papers_imported, papers_failed)
        """
        imported = 0
        failed = 0

        # Load metadata if provided
        metadata = {}
        if metadata_file and os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata file: {e}")

        # Find all PDF files in the source directory
        pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]

        for pdf_file in pdf_files:
            source_path = os.path.join(source_dir, pdf_file)

            # Try to extract paper ID from filename
            paper_id = None

            # Pattern for arXiv IDs (old and new format)
            arxiv_pattern = r'((?:\d{4}\.\d{4,5})|(?:\w+(?:-\w+)?/\d{7}))'
            match = re.search(arxiv_pattern, pdf_file)

            if match:
                paper_id = match.group(1)

            # If we have a paper ID, try to get metadata
            if paper_id:
                # Check if we have metadata for this paper
                paper_metadata = metadata.get(paper_id, {})

                if not paper_metadata:
                    # Create basic metadata
                    paper_metadata = {
                        'id': paper_id,
                        'title': pdf_file.replace('.pdf', ''),
                        'authors': [],
                        'summary': ''
                    }

                # Add the paper to the store
                success = self.add_paper(paper_metadata, source_path)

                if success:
                    imported += 1
                else:
                    failed += 1
            else:
                # We couldn't identify this as an arXiv paper
                logger.warn(f"Could not identify arXiv ID for {pdf_file}")
                failed += 1

        return (imported, failed)

    def generate_insights(self, limit: int = 100) -> Dict[str, Any]:
        """
        Generate insights about the paper collection

        Args:
            limit: Maximum number of papers to analyze

        Returns:
            Dictionary with insights data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Count total papers
            cursor.execute("SELECT COUNT(*) as count FROM papers")
            total_papers = cursor.fetchone()['count']

            # Get paper counts by year
            cursor.execute("""
            SELECT substr(published_date, 1, 4) as year, COUNT(*) as count
            FROM papers
            GROUP BY year
            ORDER BY year DESC
            """)
            papers_by_year = {row['year']: row['count'] for row in cursor.fetchall()}

            # Extract all categories
            cursor.execute("SELECT categories FROM papers")
            all_categories = cursor.fetchall()

            # Count category frequencies
            category_counts = {}
            for row in all_categories:
                categories = row['categories'].split(',')
                for category in categories:
                    category = category.strip()
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1

            # Sort categories by frequency
            top_categories = sorted(
                category_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            # Extract all authors
            cursor.execute("SELECT authors FROM papers LIMIT ?", (limit,))
            all_authors = cursor.fetchall()

            # Count author frequencies
            author_counts = {}
            for row in all_authors:
                try:
                    authors = json.loads(row['authors'])
                    for author in authors:
                        if isinstance(author, dict) and 'name' in author:
                            name = author['name']
                        else:
                            name = str(author)
                        author_counts[name] = author_counts.get(name, 0) + 1
                except:
                    continue

            # Sort authors by frequency
            top_authors = sorted(
                author_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            # Get most recent papers
            cursor.execute("""
            SELECT id, title, published_date, download_date
            FROM papers
            ORDER BY download_date DESC
            LIMIT 5
            """)
            recent_papers = [dict(row) for row in cursor.fetchall()]

            conn.close()

            # Create insights object
            insights = {
                'total_papers': total_papers,
                'papers_by_year': papers_by_year,
                'top_categories': dict(top_categories),
                'top_authors': dict(top_authors),
                'recent_papers': recent_papers
            }

            return insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                'error': str(e),
                'total_papers': 0,
                'papers_by_year': {},
                'top_categories': {},
                'top_authors': {},
                'recent_papers': []
            }

    def answer_question(self, question: str) -> str:
        """
        Answer a question about the paper collection using simple text matching

        Args:
            question: The question to answer

        Returns:
            String with the answer
        """
        try:
            # Extract key terms from question
            question_lower = question.lower()

            # Simple intent classification
            if "how many" in question_lower:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM papers")
                total_papers = cursor.fetchone()[0]
                conn.close()

                return f"There are {total_papers} papers in the collection."

            elif "recent" in question_lower or "latest" in question_lower:
                papers = self.get_all_papers(limit=5)
                if not papers:
                    return "There are no papers in the collection."

                answer = "The most recent papers are:\n"
                for i, paper in enumerate(papers, 1):
                    title = paper.get('title', 'Unknown title')
                    authors = paper.get('authors', [])
                    if isinstance(authors, list):
                        authors_str = ', '.join(authors[:3])
                        if len(authors) > 3:
                            authors_str += f" and {len(authors) - 3} more"
                    else:
                        authors_str = str(authors)

                    answer += f"{i}. {title} by {authors_str}\n"

                return answer

            elif "author" in question_lower or "who" in question_lower:
                # Search for papers by author
                search_terms = question_lower.replace("author", " ").replace("who", " ").replace("by", " ")
                papers = self.search_papers(search_terms, limit=5)

                if not papers:
                    return f"I couldn't find papers matching '{search_terms}'."

                answer = f"Found {len(papers)} papers that might match your query:\n"
                for i, paper in enumerate(papers, 1):
                    title = paper.get('title', 'Unknown title')
                    authors = paper.get('authors', [])
                    if isinstance(authors, list):
                        authors_str = ', '.join(authors[:3])
                        if len(authors) > 3:
                            authors_str += f" and {len(authors) - 3} more"
                    else:
                        authors_str = str(authors)

                    answer += f"{i}. {title} by {authors_str}\n"

                return answer

            else:
                # General search query
                papers = self.search_papers(question, limit=5)

                if not papers:
                    return f"I couldn't find papers matching '{question}'."

                answer = f"Found {len(papers)} papers that might answer your question:\n"
                for i, paper in enumerate(papers, 1):
                    title = paper.get('title', 'Unknown title')
                    abstract = paper.get('abstract', '')
                    if abstract and len(abstract) > 150:
                        abstract = abstract[:150] + "..."

                    answer += f"{i}. {title}\n"
                    if abstract:
                        answer += f"   Abstract: {abstract}\n"

                return answer

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an error trying to answer your question: {str(e)}"
