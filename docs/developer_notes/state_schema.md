# HireOS State Schema

Detailed specifications of the HireOSState TypedDict.

## Input Fields

- job_description: String
- raw_resumes: List of strings
- api_key: String

## Processing Fields

- parsed_candidates: List of parsed resumes
- scored_candidates: List of scores

## Control & Error Fields

- next_node: str
- completed_nodes: list
- error_node: Optional[str]
- error_message: Optional[str]
