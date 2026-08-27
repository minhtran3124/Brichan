"""Frozen techstack-context policy evaluation.

The package holds test-only evidence for coordinator policy. It is never
production validation, and ``src/brichan`` never imports it: the dependency
runs one way only, from this package into the production resolver.
"""
