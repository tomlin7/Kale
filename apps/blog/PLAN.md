# Web Publishing Platform & CMS (`apps/blog`) Plan

## 1. Overview
`apps/blog` is a lightweight, high-performance publishing engine and content management system written in Kale. It runs atop `libs/web` and `libs/sql` (SQLite), delivering static-like response latencies with dynamic content capabilities.

---

## 2. Directory Layout & Module Specifications

```
apps/blog/
├── models/
│   ├── post.kl          # Post struct (id, slug, title, markdown, html, published_at)
│   ├── tag.kl           # Tag relationships
│   └── user.kl          # Author metadata and authentication hashes
├── controllers/
│   ├── post_controller.kl # Post listing, slug display, RSS feed generation
│   └── admin_controller.kl# Post creation, editing, Markdown preview, draft publishing
├── views/
│   ├── layout.kl        # Master HTML shell, navigation, header, footer
│   ├── post_view.kl     # Single post rendering template
│   └── admin_view.kl    # Admin editing dashboard
├── markdown.kl          # Fast CommonMark / Markdown parser to HTML
├── main.kl              # Web server bootstrap, database migration, router attachment
└── PLAN.md
```

---

## 3. Architecture & Data Flow

```
[ HTTP Request ]
       │
       ▼
[ libs/web Router ] ──► [ controllers/post_controller ]
                               │
                               ├──► [ models/post ] ──► [ libs/sql (SQLite3) ]
                               │
                               ├──► [ markdown.kl ] (Cache rendered HTML)
                               │
                               ▼
                       [ views/post_view ]
                               │
                               ▼
                     [ HTTP 200 Response ]
```

---

## 4. Key Milestones
- [ ] SQLite schema migrations for `posts`, `tags`, and `authors`.
- [ ] Markdown parsing pipeline with code block syntax highlighting.
- [ ] Responsive frontend layout using clean typography and CSS.
- [ ] Admin dashboard for authoring new posts in real-time.
