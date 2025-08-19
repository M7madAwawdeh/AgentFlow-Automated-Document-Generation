<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AIController;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "web" middleware group. Make something great!
|
*/

Route::get('/', function () {
    return view('welcome');
});

Route::get('/ai', [AIController::class, 'dashboard'])->name('ai.dashboard');
Route::post('/ai/projects', [AIController::class, 'storeProject'])->name('ai.projects.store');
Route::post('/ai/upload-files', [AIController::class, 'uploadFiles'])->name('ai.upload.files');
Route::post('/ai/git-analysis', [AIController::class, 'gitAnalysis'])->name('ai.git.analysis');
Route::get('/ai/sessions/{session_id}/status', [AIController::class, 'getSessionStatus'])->name('ai.sessions.status');
Route::get('/ai/projects/{project_id}/documentation', [AIController::class, 'showDocumentation'])->name('ai.projects.documentation');
Route::get('/ai/projects/{project_id}/tests', [AIController::class, 'showTests'])->name('ai.projects.tests');
Route::get('/ai/projects/{project_id}/security', [AIController::class, 'showSecurity'])->name('ai.projects.security');
Route::get('/ai/projects/{project_id}/performance', [AIController::class, 'showPerformance'])->name('ai.projects.performance');
