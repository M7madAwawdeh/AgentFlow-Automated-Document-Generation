<?php

use Illuminate\Foundation\Configuration\Exceptions;

return Exceptions::configure()
    ->dontReport([
        Illuminate\Auth\AuthenticationException::class,
        Illuminate\Auth\Access\AuthorizationException::class,
        Illuminate\Database\Eloquent\ModelNotFoundException::class,
        Illuminate\Validation\ValidationException::class,
    ])
    ->dontFlash([
        'current_password',
        'password',
        'password_confirmation',
    ])
    ->renderable(function (Throwable $e) {
        //
    });
