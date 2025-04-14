from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

from query import (
    BROWSE_PHENOTYPES_QUERY,
    EVIDENCE_BROWSE_QUERY,
    EVIDENCE_SUMMARY_QUERY,
)


class CivicAPIClient:
    """
    Client for interacting with the CIViC (Clinical Interpretation of Variants in Cancer) GraphQL API.
    Provides methods to browse phenotypes, retrieve evidence, and source details in bulk.
    """

    def __init__(self, cookies=None):
        """
        Initialize the CIViC API client.

        Args:
            cookies (dict, optional): Cookies for authenticated requests.
        """
        self.base_url = "https://civicdb.org/api/graphql"
        self.cookies = cookies or {}
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
        }

    def browse_phenotype(self, phenotype_name=None):
        """
        Retrieve phenotype information from the CIViC API.

        Args:
            phenotype_name (str, optional): Name of the phenotype to browse.

        Returns:
            dict: JSON response containing phenotype data.
        """
        variables = {"phenotypeName": phenotype_name}
        payload = {
            "operationName": "BrowsePhenotypes",
            "variables": variables,
            "query": BROWSE_PHENOTYPES_QUERY,
        }
        result = self._send_request(payload)
        return result["data"]["browsePhenotypes"]["edges"][0]["node"]

    def get_sources(self, evidence_id_list):
        """
        Fetch source information for multiple evidence items in parallel.

        Args:
            evidence_id_list (list of int): List of evidence IDs.

        Returns:
            list of dict: List of source information for each evidence item.
        """
        payloads = [
            {
                "operationName": "EvidenceSummary",
                "variables": {"evidenceId": eid},
                "query": EVIDENCE_SUMMARY_QUERY,
            }
            for eid in evidence_id_list
        ]
        results = self._send_parallel_requests(payloads)
        return [res["data"]["evidenceItem"]["source"] for res in results]

    def search_evidence(
        self,
        disease_name=None,
        therapy_name=None,
        molecular_profile_name=None,
        phenotype_name=None,
        filter_strong_evidence=False,
        evidence_type=None,
        evidence_direction=None,
    ):
        """
        Search for evidence items based on filters like disease, therapy, and molecular profile.

        Args:
            disease_name (str, optional): Disease name to filter.
            therapy_name (str, optional): Therapy name to filter.
            molecular_profile_name (str, optional): Molecular profile name to filter.
            phenotype_name (str, optional): Phenotype name to filter.
            filter_strong_evidence (bool): Whether to include only strong evidence (rating > 3).
            evidence_type (str, optional): Type of evidence ("PREDICTIVE" or "DIAGNOSTIC" or "PROGNOSTIC" or "PREDISPOSING" or "FUNCTIONAL").
            evidence_direction (str, optional): Direction of evidence (SUPPORTS or DOES_NOT_SUPPORT).

        Returns:
            pd.DataFrame: DataFrame containing filtered evidence items and source information.
        """
        variables = {"sortBy": {"column": "EVIDENCE_RATING", "direction": "DESC"}}

        if evidence_type in [
            "PREDICTIVE",
            "DIAGNOSTIC",
            "PROGNOSTIC",
            "PREDISPOSING",
            "FUNCTIONAL",
        ]:
            variables["evidenceType"] = evidence_type
            if evidence_direction in ["SUPPORTS", "DOES_NOT_SUPPORT"]:
                variables["evidenceDirection"] = evidence_direction

        variables["status"] = "ACCEPTED" if filter_strong_evidence else "NON_REJECTED"

        if disease_name:
            variables["diseaseName"] = disease_name
        if therapy_name:
            variables["therapyName"] = therapy_name
        if molecular_profile_name:
            variables["molecularProfileName"] = molecular_profile_name

        phenotype_data = {"id": None, "name": None}
        if phenotype_name:
            phenotype_data = self.browse_phenotype(phenotype_name)
            variables["phenotypeId"] = phenotype_data["id"]

        payload = {
            "operationName": "EvidenceBrowse",
            "variables": variables,
            "query": EVIDENCE_BROWSE_QUERY,
        }

        results = self._send_request(payload)
        results = results["data"]["evidenceItems"]["edges"]

        data = []
        for entry in results:
            result = entry["node"]

            if filter_strong_evidence and entry["evidenceRating"] <= 3:
                continue

            evidence = {
                "id": result["id"],
                "name": result["name"],
                "disease_id": result["disease"]["id"],
                "disease_name": result["disease"]["name"],
                "therapy_ids": "+".join(
                    [str(therapy["id"]) for therapy in result["therapies"]]
                ),
                "therapy_names": "+".join(
                    [therapy["name"] for therapy in result["therapies"]]
                ),
                "molecular_profile_id": result["molecularProfile"]["id"],
                "molecular_profile_name": result["molecularProfile"]["name"],
                "gene_id": result["molecularProfile"]["parsedName"][0]["id"],
                "gene_name": result["molecularProfile"]["parsedName"][0]["name"],
                "variant_id": result["molecularProfile"]["parsedName"][1]["id"],
                "variant_name": result["molecularProfile"]["parsedName"][1]["name"],
                "phenotype_id": phenotype_data["id"],
                "phenotype_name": phenotype_data["name"],
                "description": result["description"],
                "evidence_type": result["evidenceType"],
                "evidence_direction": result["evidenceDirection"],
                "evidence_rating": result["evidenceRating"],
            }

            data.append(evidence)

        df = pd.DataFrame(data)
        df = df.dropna(subset=["evidence_rating"])
        """        

        unique_desc_df = df.drop_duplicates(subset="description", keep="last")
        unique_ids = unique_desc_df["id"].tolist()
        unique_descs = unique_desc_df["description"].tolist()

        sources = self.get_sources(unique_ids)

        citation_map = {
            unique_descs[i]: sources[i]["citation"] for i in range(len(sources))
        }
        df["citation"] = df["description"].map(citation_map)

        url_map = {
            unique_descs[i]: sources[i]["sourceUrl"] for i in range(len(sources))
        }
        df["sourceUrl"] = df["description"].map(url_map)"""

        return df

    def _send_request(self, payload):
        """
        Internal method to send a single request to the CIViC API.

        Args:
            payload (dict): GraphQL query payload.

        Returns:
            dict: Parsed JSON response from the API.
        """
        response = requests.post(
            self.base_url, headers=self.headers, cookies=self.cookies, json=payload
        )

        # Raise exception for HTTP errors
        response.raise_for_status()

        return response.json()

    def _send_parallel_requests(self, payloads, max_workers=12):
        """
        Internal method to send multiple GraphQL requests concurrently.

        Args:
            payloads (list): List of GraphQL payloads.
            max_workers (int): Number of concurrent threads (default 12).

        Returns:
            list of dict: List of API responses for each payload.
        """
        results = []

        def send(payload):
            return self._send_request(payload)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_payload = {executor.submit(send, p): p for p in payloads}
            for future in as_completed(future_to_payload):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(
                        {"error": str(e), "payload": future_to_payload[future]}
                    )

        return results


def example_usage():
    """Example of how to use the CivicAPIClient."""
    import json

    client = CivicAPIClient()
    results = client.search_evidence(
        disease_name="cancer", therapy_name="ce", molecular_profile_name="egfr"
    )
    print(results)

    # print(json.dumps(client.browse_phenotype("pain"), indent=2))
    # print(json.dumps(client.get_sources([1572, 1058, 7096]), indent=2))


if __name__ == "__main__":
    example_usage()
