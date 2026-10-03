# Local Cloudinary media storage

The Django settings load `main/.env` for local development. Configure the cloud
name and an **unsigned upload preset** in `main/.env`:

```dotenv
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_UPLOAD_PRESET=your_unsigned_preset_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Create the preset in Cloudinary Console > Settings > Upload presets. Set
**Signing Mode** to **Unsigned**, its destination folder (asset folder for
dynamic-folder accounts) to `products_images`, and restrict allowed formats
to JPG, PNG, and WebP with a 5 MB maximum file size. Admin product create/edit
forms upload images directly to Cloudinary using that preset, then Django
stores only the returned `products_images/...` public IDs. The API key and
secret are optional for these browser uploads; they can be used for other
signed Cloudinary API operations.

Without a cloud name and upload preset, Django uses local filesystem storage
for normal files and disables product image upload. Keep `.env` private; it is
excluded from Git.