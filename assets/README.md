# Diagram assets

The diagrams in this repository are written as Mermaid inside the Markdown files. **GitHub renders
those blocks natively** — you do not need these images to read the docs on github.com.

The `.png` files here exist for places that do *not* render Mermaid: LinkedIn posts, a portfolio
site, a PDF of your CV, a slide, or anyone reading the raw Markdown in a plain text editor.

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

The `.mmd` sources and the Mermaid blocks in the Markdown must be kept in sync by hand. If you
change one, change the other — a diagram that contradicts the prose is worse than no diagram.

## Why the Markdown keeps Mermaid rather than just embedding the PNG

- It renders on GitHub with a theme that follows the reader's light/dark setting; a white PNG does
  not.
- It diffs in review — a pull request shows what changed in the diagram, not "binary file changed".
- It stays editable without a rendering toolchain.

For the same reason, the diagrams use Mermaid's default colours rather than custom hex fills.
Hand-picked colours are the usual cause of a diagram that is unreadable in GitHub's dark mode.
