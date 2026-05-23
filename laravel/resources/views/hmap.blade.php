<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ config('app.name', 'H-MAP') }}</title>
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=figtree:400,500,600,700&display=swap" rel="stylesheet">
    @php
        // Laravel 8 + Vite 5 + PHP 7.4 doesn't ship with the @vite Blade
        // directive, so we read the build manifest manually. The manifest
        // path mirrors what vite outputs for resources/js/app.jsx and the
        // CSS imported through it. Falls back to a clear error in dev when
        // the build hasn't been run.
        $manifestPath = public_path('build/manifest.json');
        $manifest = file_exists($manifestPath) ? json_decode(file_get_contents($manifestPath), true) : null;
        $jsEntry = $manifest['resources/js/app.jsx'] ?? null;
        // Both resources/css/app.css (Tailwind) and any CSS chained from the
        // JS entry must be loaded. The CSS-only entry is registered separately
        // in vite.config.js so it has its own manifest entry.
        $cssEntry = $manifest['resources/css/app.css'] ?? null;
        // Asset base honors ASSET_URL (set in .env for subpath deploys
        // like /hmap), falls back to APP_URL, then to the host root.
        $base = env('ASSET_URL') ?: env('APP_URL') ?: url('');
        $assetBase = rtrim($base, '/') . '/build/';
    @endphp
    @if ($jsEntry)
        {{-- Tailwind / app.css first so chained component-scoped CSS can override --}}
        @if ($cssEntry)
            <link rel="stylesheet" href="{{ $assetBase . $cssEntry['file'] }}">
        @endif
        @foreach ($jsEntry['css'] ?? [] as $css)
            <link rel="stylesheet" href="{{ $assetBase . $css }}">
        @endforeach
        <script type="module" src="{{ $assetBase . $jsEntry['file'] }}"></script>
    @else
        <pre style="color:red">
H-MAP assets not built. Run `npm ci && npm run build` in laravel/.
        </pre>
    @endif
</head>
<body class="font-sans antialiased bg-slate-50">
    <div id="hmap-root"></div>
</body>
</html>
