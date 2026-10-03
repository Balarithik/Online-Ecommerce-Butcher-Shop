# Local Cloudinary media storage

The Django settings load `main/.env` for local development. Configure the
Cloudinary cloud name, API key, and API secret in `main/.env`:

```dotenv
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Admin product create/edit forms send images to an authenticated Django upload
endpoint. Django validates JPG, PNG, and WebP images up to 5 MB, uploads them
to the `products_images` folder using Cloudinary's signed API, and stores only
the returned `products_images/...` public IDs. The API secret stays on the
server; an unsigned upload preset is not required.

Without all three Cloudinary values, product image uploads are disabled. Keep
`.env` private; it is excluded from Git.