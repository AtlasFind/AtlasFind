# AtlasFind v1.0.4 Brand Guard Test Fix

- AWS static CDN (`awsstatic.com`) is treated as a multi-product corporate host.
- Generic `touch-icon-*` and favicon assets are rejected unless the asset itself identifies the product.
- Product names appearing only in the source page URL no longer make a generic corporate icon eligible.
