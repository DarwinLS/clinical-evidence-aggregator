import os
from Bio import Entrez
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# NCBI requires email and tool name for API access
Entrez.email = os.getenv("EMAIL", "your_email@example.com") 
Entrez.tool = "ClinicalSynthMVP"

def search_pubmed(supplement: str, max_results: int = 20):
    """
    Step 1: Get the PMIDs (IDs) of relevant studies
    Query Strategy:
    - Search for the supplement name
    - Filter for 'Clinical Trial' or 'Randomized Controlled Trial'
    - Filter for 'Humans'
    - Language: English
    """
    search_term = (
        f"{supplement} AND "
        "(Clinical Trial[Publication Type] OR Randomized Controlled Trial[Publication Type]) "
        "AND Humans[Mesh] AND English[lang]"
    )

    try:
        # esearch: searches PubMed and returns IDs
        handle = Entrez.esearch(
            db="pubmed",
            term=search_term,
            retmax=max_results,
            sort="relevance" # can be "date" if we want newest
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

def fetch_details(id_list):
    """
    Step 2: Given a list of IDs, fetch the actual Title, Abstract, and Metadata
    """
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
                    "journal": journal.get('Title', 'N/A')
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