# Data pack goes here (not in the repo)

The Campus Customs data pack is **not** committed to GitHub. Copy it into this folder so it looks like:

```
data/
├── README.md              (this file)
├── campus_customs.db      ← the given database (ORIGINAL, never modified by the app)
└── products/              ← the given product images (*.jpg, 102 files)
```

On first start the backend creates `campus_customs_new.db`, the **working copy** that the site reads and writes (accounts, chats). Run `./reset_db.sh` from `hw4/` to reset it to the original.
