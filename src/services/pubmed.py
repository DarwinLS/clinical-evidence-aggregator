import os
from Bio import Entrez
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# Email and tool name for NBCI API access
Entrez.email = os.getenv("EMAIL", "your_email@example.com") 
Entrez.tool = "ClinicalSynthMVP"

"""
Step 1: Get PMIDs of relevant studies
Query Strategy:
- Quote the supplement to avoid partial matches (e.g. "Beta" in Beta-Blockers).
- Restrict to [Title/Abstract] to ensure relevance.
- Include Meta-Analyses and Systematic Reviews.
"""
def search_pubmed(supplement: str, max_results: int = 20):
    
    # 1. QUOTES: Force exact phrase match ("Beta Alanine" vs Beta AND Alanine)
    # 2. FIELDS: Look in Title/Abstract to avoid random mentions in full text
    term_part = f'"{supplement}"[Title/Abstract]'
    
    # 3. TYPES: Expand to include high-quality review papers
    type_part = (
        "(Meta-Analysis[Publication Type] OR "
        "Systematic Review[Publication Type] OR "
        "Clinical Trial[Publication Type] OR "
        "Randomized Controlled Trial[Publication Type])"
    )
    
    # Combined Query
    search_term = f"{term_part} AND {type_part} AND Humans[Mesh] AND English[lang]"

    try:
        # esearch: searches PubMed and returns IDs
        handle = Entrez.esearch(
            db="pubmed",
            term=search_term,
            retmax=max_results,
            sort="relevance" 
        )
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        
        if not id_list:
            print(f"No studies found for {supplement}")
            return []

        return fetch_details(id_list)

    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []

"""
Step 2: Given a list of IDs, fetch the actual Title, Abstract, and Metadata
"""
def fetch_details(id_list):

    ids = ",".join(id_list)
    
    try:
        # efetch: fetches full records for the IDs
        handle = Entrez.efetch(
            db="pubmed",
            id=ids,
            retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()
        
        studies = []
        
        # parse messy XML into clean dictionaries
        for paper in records['PubmedArticle']:
            try:
                article = paper['MedlineCitation']['Article']
                journal = article.get('Journal', {})
                
                # extract title
                title = article.get('ArticleTitle', 'No Title')
                
                # extract abstract (handle inconsistent lists)
                abstract_raw = article.get('Abstract', {}).get('AbstractText', [])
                if isinstance(abstract_raw, list):
                    # join sections like "METHODS: ... RESULTS: ..."
                    abstract = " ".join([str(x) for x in abstract_raw])
                else:
                    abstract = str(abstract_raw)

                # extract year
                try:
                    year = journal.get('JournalIssue', {}).get('PubDate', {}).get('Year', 'N/A')
                except:
                    year = "N/A"

                # create clean object
                studies.append({
                    "id": str(paper['MedlineCitation']['PMID']),
                    "title": title,
                    "abstract": abstract,
                    "year": year,
                    "journal": journal.get('Title', 'N/A'),
                    # Note: We rely on the Extractor (LLM) to determine "study_type" 
                    # accurately from the abstract later, rather than parsing strict XML types here.
                })
                
            except Exception as parse_error:
                print(f"Error parsing paper: {parse_error}")
                continue

        return studies

    except Exception as e:
        print(f"Error fetching details: {e}")
        return []

# Test Block
if __name__ == "__main__":
    # only runs if executed directly
    print("Testing PubMed Fetcher...")
    results = search_pubmed("Creatine", max_results=3)
    
    for study in results:
        print(f"\n[ID: {study['id']}] {study['title'][:50]}... ({study['year']})")
        print(f"Abstract snippet: {study['abstract'][:100]}...")