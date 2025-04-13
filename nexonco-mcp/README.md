![export](assets/nexonco-mcp-banner.jpg)

<div class="title-block" style="text-align: center;" align="center">
    <b>Nexonco</b> by <a href="https://www.nexgene.ai">Nexgene Research</a> is an <a href="https://github.com/modelcontextprotocol">MCP</a> server for accessing clinical evidence from the CIViC (Clinical Interpretation of Variants in Cancer) database. It enables fast, flexible search across variants, diseases, drugs, and phenotypes to support precision oncology.
</div>

## Setup

### Prerequisites

- [uv](https://github.com/astral-sh/uv) or Docker 
- Claude Desktop (for MCP integration)

### Setup Guides

For detailed setup instructions, refer to the following documentation:

- **NANDA Host Setup**  
  See `docs/nanda-server-setup.md` for backend configuration and local registration of the NANDA Server.

- **Claude Desktop Setup**  
  See `docs/claude-desktop-setup.md` for guidance on configuring the local development environment and MCP integration.

These guides include all required steps, environment configurations, and usage notes to get up and running.

## Tool List

`search_clinical_evidence`: A MCP tool for querying clinical evidence data that returns formatted reports.

### Input Schema
The tool accepts the following optional parameters:
- **`disease_name` (str)**: Filter by disease (e.g., "Lung Non-small Cell Carcinoma").
- **`therapy_name` (str)**: Filter by therapy or drug (e.g., "Cetuximab").
- **`molecular_profile_name` (str)**: Filter by gene or variant (e.g., "EGFR L858R").
- **`phenotype_name` (str)**: Filter by phenotype (e.g., "Chest Pain").
- **`evidence_type` (str)**: Filter by evidence type (e.g., "PREDICTIVE", "DIAGNOSTIC").
- **`evidence_direction` (str)**: Filter by evidence direction (e.g., "SUPPORTS").
- **`filter_strong_evidence` (bool)**: If `True`, only includes evidence with a rating > 3 (max 5).

### Output
The tool returns a formatted string with four sections:
1. **Summary Statistics**:
   - Total evidence items
   - Average evidence rating
   - Top 3 diseases, genes, variants, therapies, and phenotypes (with counts)
2. **Top 10 Evidence Entries**:
   - Lists the highest-rated evidence items with details like disease, phenotype, gene/variant, therapy, description, type, direction, and rating.
3. **Sources & Citations**:
   - Citations and URLs for the sources of the top 10 evidence entries.
4. **Disclaimer**:
   - A note stating the tool is for research purposes only, not medical advice.


## Sample Usage 

- "Find predictive evidence for colorectal cancer therapies involving KRAS mutations."
- "Are there studies on Imatinib for leukemia?"
- "What therapies are linked to pancreatic cancer evidence?"

## Acknowledgements

- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)
- [NANDA: The Internet of AI Agents](https://nanda.media.mit.edu/)
- [CIViC - Clinical Interpretation of Variants in Cancer](https://civicdb.org)


## License

This project is licensed under the MIT License - see the <a href="LICENSE">LICENSE</a> file for details.

## Disclaimer

⚠️ This tool is intended exclusively for research purposes. It is not a substitute for professional medical advice, diagnosis, or treatment.
