# X card cache notes

Date: 2026-05-31

## Summary

Treat X post previews as cached by article URL.

When X has already generated a card for an article URL, changing only `og:image`,
`twitter:image`, image dimensions, or `twitter:card` may not refresh the preview.
Failed previews can also appear to be cached.

## Practical rule

If an article preview is cached incorrectly on X, create a fresh article URL.

Use the working portal article pattern from the start:

- keep `og:url` on the fresh article URL
- point `og:image` and `twitter:image` at an image under that same fresh article path
- use `twitter:card` value `summary`, matching older portal articles that preview correctly
- keep the old article URL alive, but remove it from the portal top page by moving its
  `meta.json` section to `archive`

## What did not help

- appending a query string to the article URL
- appending a query string to the image URL
- adding `og:image:width` / `og:image:height`
- adding `twitter:title`, `twitter:description`, or `twitter:image:alt`
- changing `summary_large_image` after X had already seen the URL

These changes may still be reasonable before X has cached the URL, but they should not
be treated as a reliable fix after a bad preview has appeared.

## Example

The access-control-matrix article was reissued several times after X cached an image-less
preview. The successful URL was:

```text
https://orange-wks.github.io/portal/articles/self-world-boundary/
```

The older URLs were left in place and moved out of the top-page recent list.
