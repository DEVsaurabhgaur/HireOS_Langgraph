# LangGraph Overview

This guide explains how LangGraph is used in the HireOS project.

## The Supervisor Node

The supervisor decides the next node in the pipeline.

## Routing logic

Routing is linear through PIPELINE_ORDER but supports fault-tolerance.

## Traversal

Nodes are executed sequentially: parse_resume, score_candidates, generate_questions, rank_candidates.

See architecture diagrams for details.
