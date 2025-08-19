<?php

namespace App\Http\Controllers;

use App\Models\Project;
use App\Models\AnalysisSession;
use App\Models\AgentOutput;
use App\Services\AIAnalysisService;
use App\Services\FileUploadService;
use App\Jobs\ProcessAIAnalysis;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;
use Illuminate\View\View;

class AIController extends Controller
{
    protected AIAnalysisService $aiService;
    protected FileUploadService $fileService;

    public function __construct(AIAnalysisService $aiService, FileUploadService $fileService)
    {
        $this->aiService = $aiService;
        $this->fileService = $fileService;
    }

    /**
     * Display the main AI analysis dashboard
     */
    public function dashboard(): View
    {
        $projects = Project::with(['analysisSessions' => function ($query) {
            $query->latest()->limit(5);
        }])->latest()->paginate(10);

        $recentSessions = AnalysisSession::with('project')
            ->latest()
            ->limit(10)
            ->get();

        $stats = [
            'total_projects' => Project::count(),
            'total_sessions' => AnalysisSession::count(),
            'completed_sessions' => AnalysisSession::where('status', 'completed')->count(),
            'failed_sessions' => AnalysisSession::where('status', 'failed')->count(),
        ];

        return view('ai.dashboard', compact('projects', 'recentSessions', 'stats'));
    }

    /**
     * Display the project creation form
     */
    public function createProject(): View
    {
        return view('ai.projects.create');
    }

    /**
     * Store a new project
     */
    public function storeProject(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'description' => 'nullable|string|max:1000',
            'git_repository' => 'nullable|url|max:500',
            'git_branch' => 'nullable|string|max:100',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $project = Project::create([
                'name' => $request->name,
                'description' => $request->description,
                'git_repository' => $request->git_repository,
                'git_branch' => $request->git_branch ?? 'main',
                'status' => 'pending',
                'configuration' => [
                    'agents' => [
                        'documenter' => true,
                        'tester' => true,
                        'security_auditor' => true,
                        'performance_optimizer' => true,
                    ],
                    'model' => 'llama-3-70b',
                    'tone' => 'professional',
                ],
            ]);

            Log::info("Project created", ['project_id' => $project->id, 'name' => $project->name]);

            return response()->json([
                'success' => true,
                'message' => 'Project created successfully',
                'project' => $project,
                'redirect_url' => route('ai.projects.show', $project->id)
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to create project", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to create project: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Display project details and analysis options
     */
    public function showProject(Project $project): View
    {
        $project->load(['analysisSessions' => function ($query) {
            $query->latest()->limit(10);
        }, 'files']);

        $latestSession = $project->analysisSessions()->latest()->first();
        
        $agentOutputs = collect();
        if ($latestSession && $latestSession->status === 'completed') {
            $agentOutputs = AgentOutput::where('project_id', $project->id)
                ->where('session_id', $latestSession->id)
                ->get()
                ->groupBy('agent_type');
        }

        return view('ai.projects.show', compact('project', 'latestSession', 'agentOutputs'));
    }

    /**
     * Display the file upload form for a project
     */
    public function uploadFiles(Project $project): View
    {
        return view('ai.projects.upload', compact('project'));
    }

    /**
     * Handle file uploads and start AI analysis
     */
    public function processUpload(Request $request, Project $project): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'files.*' => 'required|file|mimes:php,js,vue,blade.php,json,yaml,yml|max:10240',
            'agents_config' => 'nullable|array',
            'model' => 'nullable|string|in:llama-3-70b,mixtral,mistral-large',
            'tone' => 'nullable|string|in:professional,friendly,strict,mentor,casual',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            // Store uploaded files
            $uploadedFiles = $this->fileService->storeFiles($request->file('files'), $project);
            
            // Create analysis session
            $session = AnalysisSession::create([
                'project_id' => $project->id,
                'session_uuid' => Str::uuid(),
                'status' => 'started',
                'agents_config' => $request->agents_config ?? $project->configuration['agents'],
                'metadata' => [
                    'model' => $request->model ?? $project->configuration['model'],
                    'tone' => $request->tone ?? $project->configuration['tone'],
                    'files_uploaded' => count($uploadedFiles),
                    'upload_method' => 'web_upload',
                ],
            ]);

            // Update project status
            $project->update(['status' => 'analyzing']);

            // Dispatch AI analysis job
            ProcessAIAnalysis::dispatch($session, $uploadedFiles);

            Log::info("AI analysis started", [
                'project_id' => $project->id,
                'session_id' => $session->id,
                'files_count' => count($uploadedFiles)
            ]);

            return response()->json([
                'success' => true,
                'message' => 'Files uploaded and analysis started successfully',
                'session_id' => $session->session_uuid,
                'redirect_url' => route('ai.sessions.show', $session->session_uuid)
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to process upload", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to process upload: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Start analysis from Git repository
     */
    public function startGitAnalysis(Request $request, Project $project): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'git_branch' => 'nullable|string|max:100',
            'agents_config' => 'nullable|array',
            'model' => 'nullable|string|in:llama-3-70b,mixtral,mistral-large',
            'tone' => 'nullable|string|in:professional,friendly,strict,mentor,casual',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            // Clone and analyze Git repository
            $files = $this->fileService->cloneAndAnalyzeGit($project, $request->git_branch);
            
            // Create analysis session
            $session = AnalysisSession::create([
                'project_id' => $project->id,
                'session_uuid' => Str::uuid(),
                'status' => 'started',
                'agents_config' => $request->agents_config ?? $project->configuration['agents'],
                'metadata' => [
                    'model' => $request->model ?? $project->configuration['model'],
                    'tone' => $request->tone ?? $project->configuration['tone'],
                    'files_analyzed' => count($files),
                    'analysis_method' => 'git_clone',
                    'git_branch' => $request->git_branch ?? $project->git_branch,
                ],
            ]);

            // Update project status
            $project->update(['status' => 'analyzing']);

            // Dispatch AI analysis job
            ProcessAIAnalysis::dispatch($session, $files);

            Log::info("Git analysis started", [
                'project_id' => $project->id,
                'session_id' => $session->id,
                'git_branch' => $request->git_branch ?? $project->git_branch
            ]);

            return response()->json([
                'success' => true,
                'message' => 'Git analysis started successfully',
                'session_id' => $session->session_uuid,
                'redirect_url' => route('ai.sessions.show', $session->session_uuid)
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to start Git analysis", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to start Git analysis: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Display analysis session details
     */
    public function showSession(string $sessionUuid): View
    {
        $session = AnalysisSession::where('session_uuid', $sessionUuid)
            ->with(['project', 'agentOutputs'])
            ->firstOrFail();

        $agentOutputs = $session->agentOutputs->groupBy('agent_type');
        
        $progress = $this->aiService->getSessionProgress($session);

        return view('ai.sessions.show', compact('session', 'agentOutputs', 'progress'));
    }

    /**
     * Get real-time analysis status
     */
    public function getSessionStatus(string $sessionUuid): JsonResponse
    {
        try {
            $session = AnalysisSession::where('session_uuid', $sessionUuid)->firstOrFail();
            $progress = $this->aiService->getSessionProgress($session);
            
            return response()->json([
                'success' => true,
                'session' => $session,
                'progress' => $progress,
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to get session status", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to get session status: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Display documentation results
     */
    public function showDocumentation(Project $project): View
    {
        $documentation = AgentOutput::where('project_id', $project->id)
            ->where('agent_type', 'documenter')
            ->where('output_type', 'documentation')
            ->with('session')
            ->latest()
            ->get()
            ->groupBy('session_id');

        return view('ai.documentation.index', compact('project', 'documentation'));
    }

    /**
     * Display test generation results
     */
    public function showTests(Project $project): View
    {
        $tests = AgentOutput::where('project_id', $project->id)
            ->where('agent_type', 'tester')
            ->where('output_type', 'tests')
            ->with('session')
            ->latest()
            ->get()
            ->groupBy('session_id');

        return view('ai.tests.index', compact('project', 'tests'));
    }

    /**
     * Display security audit results
     */
    public function showSecurity(Project $project): View
    {
        $securityIssues = AgentOutput::where('project_id', $project->id)
            ->where('agent_type', 'security_auditor')
            ->where('output_type', 'security_report')
            ->with('session')
            ->latest()
            ->get()
            ->groupBy('session_id');

        return view('ai.security.index', compact('project', 'securityIssues'));
    }

    /**
     * Display performance optimization results
     */
    public function showPerformance(Project $project): View
    {
        $performanceIssues = AgentOutput::where('project_id', $project->id)
            ->where('agent_type', 'performance_optimizer')
            ->where('output_type', 'performance_report')
            ->with('session')
            ->latest()
            ->get()
            ->groupBy('session_id');

        return view('ai.performance.index', compact('project', 'performanceIssues'));
    }

    /**
     * Apply generated tests to the project
     */
    public function applyTests(Request $request, Project $project): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'test_ids' => 'required|array',
            'test_ids.*' => 'exists:agent_outputs,id',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $appliedTests = $this->aiService->applyGeneratedTests($request->test_ids);
            
            Log::info("Tests applied to project", [
                'project_id' => $project->id,
                'tests_applied' => count($appliedTests)
            ]);

            return response()->json([
                'success' => true,
                'message' => 'Tests applied successfully',
                'applied_tests' => $appliedTests,
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to apply tests", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to apply tests: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Export analysis results
     */
    public function exportResults(Request $request, Project $project): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'format' => 'required|string|in:pdf,markdown,json',
            'session_id' => 'nullable|exists:analysis_sessions,id',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $exportData = $this->aiService->exportResults(
                $project,
                $request->format,
                $request->session_id
            );

            return response()->json([
                'success' => true,
                'message' => 'Export completed successfully',
                'download_url' => $exportData['download_url'],
                'file_size' => $exportData['file_size'],
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to export results", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to export results: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get AI agents status
     */
    public function getAgentsStatus(): JsonResponse
    {
        try {
            $status = $this->aiService->getAgentsStatus();
            
            return response()->json([
                'success' => true,
                'agents_status' => $status,
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to get agents status", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to get agents status: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Test a specific AI agent
     */
    public function testAgent(Request $request, string $agentType): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'test_data' => 'required|array',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $testResult = $this->aiService->testAgent($agentType, $request->test_data);
            
            return response()->json([
                'success' => true,
                'message' => 'Agent test completed',
                'test_result' => $testResult,
            ]);

        } catch (\Exception $e) {
            Log::error("Failed to test agent", ['error' => $e->getMessage()]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to test agent: ' . $e->getMessage()
            ], 500);
        }
    }
}
