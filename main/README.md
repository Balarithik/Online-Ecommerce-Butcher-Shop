# Local Cloudinary media storage

The Django settings load `main/.env` for local development. Configure either
the Cloudinary account URL:

```dotenv
CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
```

or the three individual values:

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

Set the same values as environment variables in Render and redeploy. Product
image uploads are disabled unless the cloud name, API key, and API secret are
available through one of these formats. Keep `.env` private; it is excluded
from Git.

## Order confirmations

Order confirmation SMS and WhatsApp messages use Twilio's Messaging API. Add
these values to `main/.env` locally and to Render in production:

```dotenv
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_SMS_FROM=+1...
TWILIO_WHATSAPP_FROM=whatsapp:+1...
TWILIO_WHATSAPP_CONTENT_SID=HX...  # optional but recommended for production
ORDER_NOTIFICATION_COUNTRY_CODE=91
```

The SMS channel sends when `TWILIO_SMS_FROM` is configured; WhatsApp sends when
`TWILIO_WHATSAPP_FROM` is configured. For proactive production WhatsApp order
updates, use an approved Twilio Content Template and set its content SID.
