# Diagram assets

| File | Source | Used in |
|---|---|---|
| `architecture.png` | `architecture.mmd` | [README](../README.md) |
| `image-pipeline.png` | `image-pipeline.mmd` | [docs/image-pipeline.md](../docs/image-pipeline.md) |

## Regenerating

```bash
npm install @mermaid-js/mermaid-cli
npx mmdc -i assets/architecture.mmd -o assets/architecture.png -b white -w 1800
npx mmdc -i assets/image-pipeline.mmd -o assets/image-pipeline.png -b white -w 1400
```



