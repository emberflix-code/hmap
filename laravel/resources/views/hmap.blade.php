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
        $entry = $manifest['resources/js/app.jsx'] ?? null;
        $assetBase = rtrim(config('app.asset_url') ?: url(''), '/') . '/build/';
    @endphp
    @if ($entry)
        @foreach ($entry['css'] ?? [] as $css)
            <link rel="stylesheet" href="{{ $assetBase . $css }}">
        @endforeach
        <script type="module" src="{{ $assetBase . $entry['file'] }}"></script>
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
