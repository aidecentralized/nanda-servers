EVIDENCE_BROWSE_QUERY = """
query EvidenceBrowse($first: Int, $last: Int, $before: String, $after: String, $diseaseName: String, $therapyName: String, $id: Int, $description: String, $evidenceLevel: EvidenceLevel, $evidenceDirection: EvidenceDirection, $significance: EvidenceSignificance, $evidenceType: EvidenceType, $rating: Int, $variantOrigin: VariantOrigin, $variantId: Int, $molecularProfileId: Int, $assertionId: Int, $organizationId: [Int!], $includeSubgroups: Boolean, $userId: Int, $sortBy: EvidenceSort, $phenotypeId: Int, $diseaseId: Int, $therapyId: Int, $sourceId: Int, $clinicalTrialId: Int, $molecularProfileName: String, $status: EvidenceStatusFilter) {
    evidenceItems(
    first: $first
    last: $last
    before: $before
    after: $after
    diseaseName: $diseaseName
    therapyName: $therapyName
    id: $id
    description: $description
    evidenceLevel: $evidenceLevel
    evidenceDirection: $evidenceDirection
    significance: $significance
    evidenceType: $evidenceType
    evidenceRating: $rating
    variantOrigin: $variantOrigin
    variantId: $variantId
    molecularProfileId: $molecularProfileId
    assertionId: $assertionId
    organization: {ids: $organizationId, includeSubgroups: $includeSubgroups}
    userId: $userId
    phenotypeId: $phenotypeId
    diseaseId: $diseaseId
    therapyId: $therapyId
    sourceId: $sourceId
    clinicalTrialId: $clinicalTrialId
    molecularProfileName: $molecularProfileName
    status: $status
    sortBy: $sortBy
    ) {
    totalCount
    pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
    }
    edges {
        node {
        ...EvidenceGridFields
        }
    }
    }
}

fragment EvidenceGridFields on EvidenceItem {
    id
    name
    disease {
    id
    name
    }
    therapies {
    id
    name
    }
    molecularProfile {
    id
    name
    parsedName {
        ...MolecularProfileParsedName
    }
    }
    status
    description
    evidenceType
    evidenceDirection
    evidenceRating
}

fragment MolecularProfileParsedName on MolecularProfileSegment {
    ... on MolecularProfileTextSegment {
    text
    }
    ... on Feature {
    id
    name
    }
    ... on Variant {
    id
    name
    }
}
"""

BROWSE_PHENOTYPES_QUERY = """
query BrowsePhenotypes($phenotypeName: String) {
    browsePhenotypes(name: $phenotypeName, sortBy: {direction: DESC, column: EVIDENCE_ITEM_COUNT}) {
        edges {
            node {
                id
                name
                evidenceCount
            }
        }
    }
}
"""

EVIDENCE_SUMMARY_QUERY = """
query EvidenceSummary($evidenceId: Int!) {
    evidenceItem(id: $evidenceId) {
        source {
            citation
            sourceUrl
        }
        
    }
}
"""
