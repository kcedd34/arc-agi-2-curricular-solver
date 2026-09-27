"""Stage 0 initial verification routine, PRD Section 14.

Runs six probes without aborting on the first failure, classifies each as
confirmed_present, confirmed_absent, or inconclusive, and writes
docs/curriculum/verification.md. Any inconclusive result blocks Stage 0.
"""
