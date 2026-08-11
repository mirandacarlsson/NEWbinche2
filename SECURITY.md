# Security Policy

## Reporting Security Vulnerabilities

We take the security of ChEBI-N seriously. If you discover a security vulnerability,
please **do not** open a public GitHub issue. Instead, please report it responsibly by
emailing us at security@example.com with details about the vulnerability.

When reporting a security issue, please include:

- A description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Any known workarounds
- Your contact information

We will acknowledge receipt of your vulnerability report and work with you to
understand and address the issue.

## Security Considerations

### Data Integrity

This project implements algorithms for chemical enrichment analysis. When using
results for publication or critical applications:

- Validate results independently with test data
- Be aware of edge cases documented in the test suite
- Verify ontology data freshness from original ChEBI sources

### Input Validation

All input validation should be performed by applications using this library:

- Validate ChEBI IDs before passing to enrichment functions
- Ensure proper authentication for private data
- Sanitize any user-supplied inputs

### Dependency Security

This project uses:

- Regular dependency auditing via `deptry`
- Pre-commit hooks via `prek`
- Type checking with `pyright`

To update dependencies securely:

```bash
uv sync  # Update to latest pinned versions
uv run prek --all-files  # Run all quality checks
uv run pytest tests/  # Run full test suite
```

### Supported Versions

| Version | Status | Support |
|---------|--------|---------|
| 0.1.x   | Active | Security fixes |

Security fixes will be provided for the current version. We recommend
upgrading to the latest version to receive security updates.

## Security Best Practices

When using ChEBI-N in your applications:

1. **Keep dependencies updated**: Regularly run `uv sync` and review dependency updates
2. **Use virtual environments**: Always use isolated Python environments
3. **Validate inputs**: Verify all inputs to enrichment functions
4. **Test thoroughly**: Run the full test suite before deployment
5. **Monitor alerts**: Watch for security advisories from dependencies

## External Security Dependencies

This project depends on external services and data:

- **ChEBI Ontology**: Downloaded during data preparation
- **Wikidata**: Used for narrow background mappings
- **SMILES Processing**: Via RDKit library

Ensure you understand the security and licensing implications of using external
chemical data sources.

## Additional Security Resources

- Python Security Best Practices: https://python.readthedocs.io/en/latest/library/security_warnings.html
- RDKit Security: https://www.rdkit.org/docs/
- Dependency Management with uv: https://docs.astral.sh/uv/

## Security Incident Response

If a security vulnerability is discovered in ChEBI-N:

1. The vulnerability will be assessed and confirmed
2. A fix will be developed and tested
3. A security advisory will be issued
4. Users will be notified to update

For additional security information or to report a vulnerability,
contact the maintainers directly.
