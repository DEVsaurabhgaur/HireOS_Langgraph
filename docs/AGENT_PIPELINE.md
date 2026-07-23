# HireOS Multi-Agent Pipeline Architecture

Built on LangGraph, the pipeline executes sequential nodes:
1. `extractor_node`: Raw resume clean up & parsing.
2. `analyzer_node`: ATS scoring & missing keyword detection.
3. `rewriter_node`: Bullet point metric enrichment.
