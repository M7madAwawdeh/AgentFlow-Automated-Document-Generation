<?php

return [
    'web' => [
        Illuminate\Cookie\Middleware\EncryptCookies::class,
        Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse::class,
        Illuminate\Session\Middleware\StartSession::class,
        Illuminate\View\Middleware\ShareErrorsFromSession::class,
        Illuminate\Foundation\Http\Middleware\VerifyCsrfToken::class,
        Illuminate\Routing\Middleware\SubstituteBindings::class,
    ],
    'api' => [
        Illuminate\Routing\Middleware\ThrottleRequests::class.':api',
        Illuminate\Routing\Middleware\SubstituteBindings::class,
    ],
];
