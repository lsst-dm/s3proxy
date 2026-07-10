### Bug fixes

- Allow HiPS metadata and astronomy file types blocked by the MIME filter in 2.0.0: extensionless `properties` files, FITS (`.fits`, `.fits.fz`), XML metadata, and VOTable (`.vot`).
- Make extensionless-basename and suffix MIME mappings configurable via `S3PROXY_EXTENSIONLESS_MIMETYPES` and `S3PROXY_SUFFIX_MIMETYPES`.
