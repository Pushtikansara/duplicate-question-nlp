---
name: nginx
description: Use when configuring Nginx as web server or reverse proxy. Covers configuration, load balancing, caching, SSL, and security.
---

# Nginx Skill

## Instructions

Nginx (engine-x) is a high-performance HTTP server, reverse proxy, load balancer, and mail proxy. It is known for its stability, rich feature set, simple configuration, and low resource consumption. This skill covers Nginx configuration for web serving, reverse proxying, load balancing, caching, SSL/TLS, and security hardening.

### Core Concepts

Nginx uses an event-driven, asynchronous architecture that provides predictable performance under load. Configuration is organized into blocks:

- **main**: Global settings (process management, logging, etc.)
- **events**: Connection processing settings
- **http**: HTTP server configuration
- **server**: Virtual host configuration
- **location**: URL path-specific directives
- **upstream**: Backend server group for load balancing

### Basic Server Block

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    root /var/www/example.com/public;
    index index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### File Structure

Nginx configuration is typically organized as:

```
/etc/nginx/
  nginx.conf          # Main configuration
  sites-enabled/      # Enabled virtual hosts
  sites-available/    # Available virtual hosts (symlinked)
  conf.d/             # Additional configuration fragments
  modules-enabled/    # Enabled dynamic modules
```

### Configuration Directives

Directives come in two forms:
- **Simple directives**: `directive_name parameter;`
- **Block directives**: `directive_name { ... }`

Directives inherit from parent blocks unless overridden. Use the `include` directive to split configuration into manageable files.

## Examples

### Example 1: Static Website with SSL

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling on;
    ssl_stapling_verify on;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    root /var/www/example.com/public;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 256;
    gzip_vary on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2?|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Security: block access to sensitive files
    location ~* (\.env|\.git|composer\.json|package\.json|yarn\.lock)$ {
        deny all;
        return 404;
    }
}
```

### Example 2: Reverse Proxy for Node.js API

```nginx
upstream api_servers {
    least_conn;
    server 10.0.1.10:3000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:3000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:3000 max_fails=3 fail_timeout=30s backup;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/nginx/ssl/api.example.com.crt;
    ssl_certificate_key /etc/nginx/ssl/api.example.com.key;

    # Proxy settings
    location / {
        proxy_pass http://api_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 16k;
        proxy_busy_buffers_size 64k;

        # Retry on error
        proxy_next_upstream error timeout http_500 http_502 http_503;

        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://api_servers/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
```

### Example 3: Load Balancing with Multiple Upstreams

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate /etc/nginx/ssl/app.example.com.crt;
    ssl_certificate_key /etc/nginx/ssl/app.example.com.key;

    # Upstream backends for the application
    upstream app_backend {
        # Load balancing methods: least_conn, ip_hash, random, round_robin (default)
        least_conn;
        zone app_backend 64k;

        server app1.internal:8080 weight=3 max_fails=3 fail_timeout=30s;
        server app2.internal:8080 weight=2 max_fails=3 fail_timeout=30s;
        server app3.internal:8080 weight=1 max_fails=3 fail_timeout=30s;
        # Backup server handles traffic when all primary servers are down
        server app-backup.internal:8080 backup;
    }

    # WebSocket upstream
    upstream ws_backend {
        ip_hash;  # Sticky sessions for WebSocket
        server ws1.internal:3001;
        server ws2.internal:3001;
    }

    # API requests
    location /api/ {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://ws_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
    }

    # Static files served directly by Nginx
    location /static/ {
        root /var/www/app;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
}
```

### Example 4: Caching Configuration

```nginx
# Cache path definition
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m
                 max_size=10g inactive=60m use_temp_path=off;

# FastCGI cache path (for PHP/WordPress)
fastcgi_cache_path /var/cache/nginx/fastcgi levels=1:2
                   keys_zone=wordpress:256m inactive=60m;

server {
    listen 443 ssl;
    server_name blog.example.com;

    # Cache bypass for logged-in/admin users
    set $skip_cache 0;

    # POST requests and URLs with query strings should be no-cache
    if ($request_method = POST) {
        set $skip_cache 1;
    }
    if ($query_string != "") {
        set $skip_cache 1;
    }

    # Admin and login pages should not be cached
    location ~* (/wp-admin|/wp-login|/login|/cart|/checkout) {
        set $skip_cache 1;
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }

    location / {
        proxy_pass http://backend;
        proxy_cache my_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        proxy_cache_valid 200 301 302 10m;
        proxy_cache_valid 404 1m;
        proxy_cache_valid any 1m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_background_update on;
        proxy_cache_lock on;
        proxy_cache_bypass $skip_cache;
        proxy_no_cache $skip_cache;
        add_header X-Cache-Status $upstream_cache_status;
    }

    # Purge cache (requires ngx_cache_purge module or custom solution)
    location ~ /purge(/.*) {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_cache_purge my_cache "$scheme$request_method$host$1";
    }
}
```

### Example 5: Media Streaming Server

```nginx
# RTMP module configuration
rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application live {
            live on;
            record off;

            # HLS configuration
            hls on;
            hls_path /var/www/hls;
            hls_fragment 5s;
            hls_playlist_length 30s;

            # Authentication
            on_publish http://auth.example.com/stream-auth;
        }
    }
}

server {
    listen 443 ssl http2;
    server_name video.example.com;

    location /hls {
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
        }
        root /var/www;
        add_header Cache-Control no-cache;
        add_header Access-Control-Allow-Origin *;

        # CORS for media players
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'Range,DNT,X-CustomHeader,Keep-Alive,User-Agent';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Adaptive bitrate streaming directory
    location /dash {
        root /var/www;
        add_header Cache-Control no-cache;
        add_header Access-Control-Allow-Origin *;
    }
}
```

### Example 6: Microservices API Gateway

```nginx
upstream user_service {
    server user-svc:8081;
}

upstream order_service {
    server order-svc:8082;
}

upstream payment_service {
    server payment-svc:8083;
}

upstream notification_service {
    server notif-svc:8084;
}

server {
    listen 443 ssl http2;
    server_name gateway.example.com;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/s;

    # User service
    location /api/v1/users/ {
        limit_req zone=api burst=50;
        proxy_pass http://user_service;
        proxy_set_header X-Original-URI $request_uri;
    }

    # Order service
    location /api/v1/orders/ {
        limit_req zone=api burst=30;
        proxy_pass http://order_service;
        proxy_set_header X-Original-URI $request_uri;
    }

    # Payment service (higher security)
    location /api/v1/payments/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://payment_service;

        # Additional security for payment endpoints
        proxy_set_header X-Original-URI $request_uri;
        add_header X-Content-Type-Options "nosniff" always;

        # Logging
        access_log /var/log/nginx/payments.log payment_format;
    }

    # Notification service
    location /api/v1/notifications/ {
        limit_req zone=api burst=50;
        proxy_pass http://notification_service;
        proxy_set_header X-Original-URI $request_uri;
    }

    # Authentication endpoint
    location /api/v1/auth/ {
        limit_req zone=auth burst=3 nodelay;
        proxy_pass http://user_service;
    }
}
```

### Example 7: WordPress with FastCGI Cache

```nginx
server {
    listen 443 ssl http2;
    server_name blog.example.com;

    root /var/www/wordpress;
    index index.php;

    # FastCGI cache zone
    fastcgi_cache_path /var/run/nginx-cache levels=1:2 keys_zone=WORDPRESS:100m
                       inactive=60m max_size=1g;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/blog.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/blog.example.com/privkey.pem;

    # WordPress-specific rewrites
    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;

        # FastCGI cache
        fastcgi_cache WORDPRESS;
        fastcgi_cache_valid 200 60m;
        fastcgi_cache_use_stale error timeout updating invalid_header http_500;
        fastcgi_cache_methods GET HEAD;
        fastcgi_cache_bypass $http_x_cache_bypass;
        fastcgi_no_cache $http_x_no_cache;
        add_header X-FastCGI-Cache $upstream_cache_status;
    }

    # Deny access to sensitive WordPress files
    location ~* /(wp-config\.php|wp-content/uploads/.*\.php|xmlrpc\.php) {
        deny all;
        return 404;
    }

    # Cache static files aggressively
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        log_not_found off;
    }
}
```

## Best Practices

### Performance Practices

- Enable `sendfile`, `tcp_nopush`, and `tcp_nodelay` for optimal file serving
- Configure `worker_processes auto` to match CPU cores
- Set `worker_connections` to at least 1024 for moderate traffic
- Enable gzip compression for text-based responses
- Implement caching with `proxy_cache` or `fastcgi_cache`
- Use HTTP/2 for multiplexed, compressed connections
- Set appropriate buffer sizes for upstream proxying
- Configure `open_file_cache` for frequently accessed files
- Use `ssl_session_cache` to reduce SSL handshake overhead
- Enable `staple` for OCSP response caching

### Security Practices

- Disable server tokens with `server_tokens off`
- Set secure SSL protocols and ciphers
- Enable HSTS with `add_header Strict-Transport-Security`
- Set security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Implement rate limiting with `limit_req_zone` and `limit_conn_zone`
- Restrict access to sensitive locations with `allow/deny`
- Use `proxy_hide_header` to remove server version headers
- Limit request body size with `client_max_body_size`
- Disable insecure HTTP methods if not needed
- Use `ssl_stapling` for better TLS security
- Regularly update Nginx for security patches

### Maintenance Practices

- Test configuration before reload: `nginx -t`
- Use `nginx -s reload` for zero-downtime configuration changes
- Monitor access and error logs regularly
- Set up log rotation for access and error logs
- Use `include` to organize configuration into modular files
- Version control Nginx configuration files
- Benchmark with tools like `ab`, `wrk`, or `hey`
- Monitor active connections with `nginx -s status` or stub status module

## Common Mistakes

- **Not testing configuration**: Applying invalid configuration with `nginx -s reload` can cause Nginx to fail. Always run `nginx -t` first.
- **Missing upstream server health checks**: Without health checks, traffic is sent to failed upstream servers. Configure `max_fails` and `fail_timeout`.
- **Incorrect `proxy_pass` trailing slash**: `proxy_pass http://backend;` vs `proxy_pass http://backend/;` behave differently with URI handling.
- **Overly permissive security headers**: Some security headers can break legitimate functionality. Test headers thoroughly.
- **Not setting `worker_processes`**: Single-worker process cannot utilize multi-core CPUs. Set to `auto` or match CPU count.
- **Insufficient buffer sizes**: Proxying large headers or responses can cause 502 errors. Configure appropriate buffer sizes.
- **Ignoring log files**: Access and error logs contain crucial debugging information. Monitor them proactively.
- **Using default SSL settings**: Default SSL settings often include weak ciphers or old TLS versions. Explicitly configure strong settings.
- **Not configuring rate limiting**: Without rate limiting, Nginx is vulnerable to brute-force attacks and DoS.
- **Storing SSL certificates insecurely**: Certificate private keys should have restricted file permissions (600) and be stored securely.

## Libraries

### Nginx Modules

| Module | Purpose |
|--------|---------|
| ngx_http_core_module | Core HTTP functionality |
| ngx_http_ssl_module | SSL/TLS support |
| ngx_http_proxy_module | Reverse proxy functionality |
| ngx_http_upstream_module | Load balancing and upstream configuration |
| ngx_http_cache_module | Caching of proxied content |
| ngx_http_fastcgi_module | FastCGI proxying (PHP, Python) |
| ngx_http_rewrite_module | URL rewriting |
| ngx_http_gzip_module | Response compression |
| ngx_http_headers_module | Custom response headers |
| ngx_http_limit_req_module | Request rate limiting |
| ngx_http_limit_conn_module | Connection limiting |
| ngx_http_stub_status_module | Basic status information |
| ngx_http_auth_basic_module | HTTP Basic authentication |
| ngx_http_geo_module | Geographic-based configuration |
| ngx_http_map_module | Variable mapping |
| ngx_http_log_module | Custom log formats |

### Third-Party Modules

| Module | Purpose |
|--------|---------|
| ngx_cache_purge | Cache purging functionality |
| nginx-module-vts | Virtual host traffic status |
| nginx-push-stream-module | Server-sent events and streaming |
| nginx-rtmp-module | RTMP streaming support |
| headers-more-nginx-module | Advanced header manipulation |
| lua-nginx-module | Lua scripting within Nginx |
| ngx_brotli | Brotli compression support |

## Design Principles

### Event-Driven Architecture

Nginx's event-driven, non-blocking architecture handles thousands of concurrent connections with minimal resource usage. Configuration should respect this: avoid blocking operations, minimize disk I/O in request paths, and prefer asynchronous upstream connections.

### Layered Configuration

Configuration should be layered: global defaults in `nginx.conf`, shared settings in `conf.d/`, and site-specific configurations in `sites-available/`. Each layer overrides the parent, enabling clear separation of concerns.

### Security First, Performance Second

Security should never be sacrificed for performance. Default deny for access control, explicit allow for permitted traffic. Use defense in depth: network-level security, TLS, security headers, rate limiting, and input validation at the proxy level.

### Stateless Proxying

Design Nginx configuration to be stateless where possible. Avoid sticky sessions for load balancing unless required by the application. Stateless configurations scale horizontally without complexity.

## Coding Standards

### Configuration Layout

```
nginx/
  nginx.conf                  # Main configuration
  sites-available/
    example.com               # Virtual host config (symlink to sites-enabled)
    api.example.com
  conf.d/
    ssl.conf                  # SSL/TLS configuration
    security.conf             # Security headers
    gzip.conf                 # Compression settings
    cache.conf                # Caching configuration
    rate-limit.conf           # Rate limiting zones
  snippets/
    fastcgi-php.conf          # PHP FastCGI configuration
    proxy-defaults.conf       # Default proxy settings
```

### Naming Conventions

- Configuration files: `kebab-case` matching the server name (e.g., `example.com`, `api-internal`)
- Upstream names: descriptive and lowercase (e.g., `api_backend`, `app_servers`)
- Cache zones: uppercase descriptive name (e.g., `MY_CACHE`, `WORDPRESS`)
- Rate limit zones: descriptive (e.g., `api_limit`, `auth_limit`)

### Configuration Formatting

```nginx
# Indentation: 4 spaces
# Block directives open on the same line as the directive name
# Closing brace aligns with the opening directive

server {
    # Simple directives grouped logically
    listen 443 ssl http2;
    server_name example.com;

    # SSL configuration group
    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Location blocks sorted by path specificity
    location / {
        proxy_pass http://backend;
    }

    location /static/ {
        root /var/www;
        expires 1y;
    }

    # Regex locations (order matters)
    location ~* \.(css|js)$ {
        expires max;
    }
}
```
